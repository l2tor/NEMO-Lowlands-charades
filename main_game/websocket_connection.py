from threading import Thread

from websocket_server import WebsocketServer

# @TODO: create a way to exit thread (via Ctrl+C)
# @TODO: synchronization with other threads needed?
class WebsocketConnection(Thread):
	def __init__(self, port, message_received_callback):
		Thread.__init__(self)
		self.port = port
		self.num_clients_connected = 0
		self.message_received_callback = message_received_callback

	def run(self):
		print "starting web socket..."
		self.websocket_server = WebsocketServer(self.port, "")
		self.websocket_server.set_fn_new_client(self._new_web_client)
		self.websocket_server.set_fn_client_left(self._web_client_left)
		self.websocket_server.set_fn_message_received(self._web_message_received)

		try:
			self.websocket_server.run_forever()
		except:
			print "Exception"

	def stop(self):
		# @TODO: okay, this is not super clean but seems to work for now with an exception popping up...
		print "Stopping web server..."
		self.websocket_server.server_close()

	def is_client_connected(self):
		return self.num_clients_connected > 0

	def send(self, message):
		self.websocket_server.send_message_to_all(message)

	def _new_web_client(self, client, server):
		print "New client connected via web"
		self.num_clients_connected += 1

	def _web_client_left(self, client, server):
		print "Web client disconnected"
		self.num_clients_connected -= 1

	def _web_message_received(self, client, server, message):
		print "Message received from web client: " + message 
		self.message_received_callback("web", message)    

