using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

namespace GestureShared
{
    public class SocketConnection
    {
        private Socket client = null;
        private string clientName = "";
        private Action<string, string> callback;
        private Action disconnectCallback;

        // State object for receiving data from remote device.  
        public class StateObject
        {
            // Client socket.  
            public Socket workSocket = null;
            // Size of receive buffer.  
            public const int BufferSize = 256;
            // Receive buffer.  
            public byte[] buffer = new byte[BufferSize];
            // Received data string.  
            public StringBuilder sb = new StringBuilder();
        }

        public SocketConnection(Action<string, string> callback, Action disconnectCallback = null)
        {
            this.callback = callback;
            this.disconnectCallback = disconnectCallback;
        }

        public void Connect(string clientName, string ip, int port)
        {
            this.clientName = clientName;
            IPAddress ipAddress = IPAddress.Parse(ip);
            IPEndPoint remoteEP = new IPEndPoint(ipAddress, port);
            this.client = new Socket(ipAddress.AddressFamily, SocketType.Stream, ProtocolType.Tcp);
            this.client.Connect(remoteEP);
            this.Send("register");
            this.Poll();
        }

        public void Send(string data, String target = "")
        {
            string dataToSend = this.clientName + ":";

            if (target != "")
            {
                dataToSend += target + ":";
            }

           dataToSend += data + "#";

            byte[] byteData = Encoding.ASCII.GetBytes(dataToSend);
            this.client.Send(byteData, 0, byteData.Length, 0);
        }

        public void Poll()
        {
            try
            {
                // Create the state object.  
                StateObject state = new StateObject();
                state.workSocket = this.client;

                // Begin receiving the data from the remote device.  
                client.BeginReceive(state.buffer, 0, StateObject.BufferSize, 0,
                    new AsyncCallback(ReceiveCallback), state);
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());

                if (this.disconnectCallback != null)
                    this.disconnectCallback();
            }
        }

        private string[] ExtractOriginMessage(string data)
        {
            data = data.Substring(0, data.Length-1);

            string[] parts = data.Split(':');
            if (parts.Length == 2)
                return new string[] { parts[0], parts[1] };
            else
                return new string[] { parts[0], parts[2] };
        }

        private void ReceiveCallback(IAsyncResult ar)
        {
            try
            {
                // Retrieve the state object and the client socket   
                // from the asynchronous state object.  
                StateObject state = (StateObject)ar.AsyncState;
                Socket client = state.workSocket;

                // Read data from the remote device.  
                int bytesRead = client.EndReceive(ar);

                if (bytesRead > 0)
                {
                    string data = Encoding.ASCII.GetString(state.buffer, 0, bytesRead);
                    string[] split = data.Split('#');
                    int endTokenIndex = data.IndexOf('#');

                    if (split[1] != "")
                    {
                        state.sb.Append(split[0]);
                        string[] toReturn = this.ExtractOriginMessage(state.sb.ToString());
                        this.callback(toReturn[0], toReturn[1]);

                        for (int i = 1; i < split.Length-1; i++)
                        {
                            toReturn = this.ExtractOriginMessage(split[i]);
                            this.callback(toReturn[0], toReturn[1]);
                        }

                        state.sb.Clear();
                        state.sb.Append(split[split.Length - 1]);
                    }

                    else if (split[1] == "" && endTokenIndex != -1)
                    {
                        state.sb.Append(data);
                        string[] toReturn = this.ExtractOriginMessage(state.sb.ToString());
                        this.callback(toReturn[0], toReturn[1]);
                        state.sb.Clear();
                    }

                    else
                    {
                        state.sb.Append(data);
                    }
                    
                    // There might be more data, so store the data received so far.  
                    //state.sb.Append(Encoding.ASCII.GetString(state.buffer, 0, bytesRead));

                    // Get the rest of the data.  
                    client.BeginReceive(state.buffer, 0, StateObject.BufferSize, 0,
                        new AsyncCallback(ReceiveCallback), state);
                }
                else
                {
                    /*
                    // All the data has arrived; put it in response.  
                    if (state.sb.Length > 1)
                    {
                        response = state.sb.ToString();
                    }
                    // Signal that all bytes have been received.  
                    receiveDone.Set();*/
                }
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
                if (this.disconnectCallback != null)
                    this.disconnectCallback();
            }
        }
    }
}
