import json
from decimal import Decimal, InvalidOperation

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction

from .models import ChatRoom, AuctionItem

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.user = self.scope['user'] # User from AuthMiddlewareStack

        # 1. Verification: Is the user part of this project?
        is_authorized = await self.check_user_auth(self.room_id, self.user)

        if self.user.is_authenticated and is_authorized:
            self.room_group_name = f'chat_{self.room_id}'
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            # Reject the connection if they aren't authorized
            await self.close()

    @database_sync_to_async
    def check_user_auth(self, room_id, user):
        try:
            room = ChatRoom.objects.get(id=room_id)
            project = room.project
            # Only the client or the assigned freelancer can enter
            return user == project.client or user == project.freelancer
        except ChatRoom.DoesNotExist:
            return False

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        # Save the message to the database
        await self.save_message(message)

        # Broadcast the message to everyone in the chat room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.user.username,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))

    @database_sync_to_async
    def save_message(self, message):
        from .models import Message
        chat_room = ChatRoom.objects.get(id=self.room_id)
        Message.objects.create(
            room=chat_room,
            sender=self.user,
            content=message
        )


class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.room_group_name = "auction_room"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        item = await self.get_active_item()
        if item:
            await self.send(text_data=json.dumps({
                "type": "current_price",
                "price": str(item.current_price),
                "title": item.title,
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("type") != "place_bid":
            return

        amount = data.get("amount")
        try:
            bid_amount = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            await self.send(text_data=json.dumps({
                "type": "bid_rejected",
                "reason": "invalid_amount",
            }))
            return

        result = await self.place_bid(bid_amount, self.user)
        if result is None:
            await self.send(text_data=json.dumps({
                "type": "bid_rejected",
                "reason": "no_active_item",
            }))
            return

        if not result["accepted"]:
            await self.send(text_data=json.dumps({
                "type": "bid_rejected",
                "reason": "bid_too_low",
                "current_price": str(result["current_price"]),
            }))
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "new_highest_bid",
                "price": str(result["current_price"]),
                "winner": result["winner"],
            }
        )

    async def new_highest_bid(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_highest_bid",
            "price": event["price"],
            "winner": event["winner"],
        }))

    @database_sync_to_async
    def get_active_item(self):
        return AuctionItem.objects.filter(is_active=True).order_by("id").first()

    @database_sync_to_async
    def place_bid(self, bid_amount, user):
        with transaction.atomic():
            item = AuctionItem.objects.select_for_update().filter(is_active=True).order_by("id").first()
            if not item:
                return None

            if bid_amount <= item.current_price:
                return {
                    "accepted": False,
                    "current_price": item.current_price,
                }

            item.current_price = bid_amount
            item.highest_bidder = user
            item.save(update_fields=["current_price", "highest_bidder"])

            return {
                "accepted": True,
                "current_price": item.current_price,
                "winner": user.username,
            }
