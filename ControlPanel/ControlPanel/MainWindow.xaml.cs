using GestureShared;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.Windows.Threading;

namespace ControlPanel
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private Process procMainGame;
        private SocketConnection socket;
        private bool connecting = true;

        public MainWindow()
        {
            InitializeComponent();
            Closing += new System.ComponentModel.CancelEventHandler(MainWindow_Closing);
        }

        private void Button_Click(object sender, RoutedEventArgs e)
        {
            // Start the Python script for the main game (which we can connect to via socket)
            StartMainGame();
            
            // Connect via socket and make ourselves known
            ConnectToSocket();

            // Start the Kinect recorder
            StartKinectRecordingTool();

            btnConnect.IsEnabled = false;

            // Update the list of connected modules
            DispatcherTimer t = new DispatcherTimer();
            t.Tick += new EventHandler(timer_Tick);
            t.Interval = new TimeSpan(0, 0, 5);
            t.Start();
        }

        private void timer_Tick(object sender, EventArgs e)
        {
            // Get list of connected modules from the main game
            this.socket.Send("get_connected_clients(controlpanel)", "maingame");
        }

        private void StartKinectRecordingTool()
        {
            string exe_dir = System.Reflection.Assembly.GetEntryAssembly().Location;
            exe_dir = exe_dir.Substring(0, exe_dir.IndexOf(System.IO.Path.GetFileName(exe_dir)));

            Process procKinect = new Process();

            procKinect.StartInfo.WorkingDirectory = exe_dir + "..\\..\\..\\..\\KinectRecorder\\bin\\x64\\Release\\";
            procKinect.StartInfo.FileName = "KinectRecorder.exe";

            try
            {
                procKinect.Start();
            }

            catch (Exception ex)
            {

            }            
        }

        private void StartMainGame()
        {
            string exe_dir = System.Reflection.Assembly.GetEntryAssembly().Location;
            exe_dir = exe_dir.Substring(0, exe_dir.IndexOf(System.IO.Path.GetFileName(exe_dir)));

            procMainGame = new Process();

            // The qi-url parameter is specific to the NAO robot, might have to be updated if you use a different robot
            string command = "python -m main_game.main_game --qi-url=" + txtIP.Text;
            procMainGame.StartInfo.UseShellExecute = true;

            procMainGame.StartInfo.WorkingDirectory = exe_dir + "..\\..\\..\\..\\";

            procMainGame.StartInfo.FileName = @"C:\Windows\System32\cmd.exe";
            //psi.Verb = "runas";
            procMainGame.StartInfo.Arguments = "/c " + command;
            procMainGame.StartInfo.RedirectStandardInput = false;
            procMainGame.StartInfo.RedirectStandardOutput = false;
            //proc1.WindowStyle = ProcessWindowStyle.Hidden;
            procMainGame.Start();
        }

        // Incoming message from the socket
        private void MessageReceived(string sender, string content)
        {
            string method = content;
            object[] parameters = null;

            // Try to call the function
            if (content.IndexOf('(') != -1)
            {
                parameters = content.Substring(content.IndexOf('(') + 1, content.IndexOf(')') - content.IndexOf('(') - 1).Split(',');
                for (int i = 0; i < parameters.Length; i++)
                {
                    parameters[i] = ((string)parameters[i]).Trim();
                }

                method = content.Substring(0, content.IndexOf('('));
            }

            MethodInfo mi = this.GetType().GetMethod(method);
            mi.Invoke(this, parameters);
        }

        public void update_connected_clients(string clients)
        {
            // Callback for the timer to check status of connected modules
            Application.Current.Dispatcher.Invoke(new Action(() => { 

                string[] clientparts = clients.Split(';');

                if (clientparts.Contains("kinectrecorder"))
                {
                    lblKinectRecorder.Foreground = new SolidColorBrush(Colors.Green);
                }
                else
                {
                    lblKinectRecorder.Foreground = new SolidColorBrush(Colors.Red);
                }

                if (clientparts.Contains("controlpanel"))
                {
                    lblMainGame.Foreground = new SolidColorBrush(Colors.Green);
                }
                else
                {
                    lblMainGame.Foreground = new SolidColorBrush(Colors.Red);
                }

                if (clientparts.Contains("webclient"))
                {
                    lblTabletGame.Foreground = new SolidColorBrush(Colors.Green);
                }
                else
                {
                    lblTabletGame.Foreground = new SolidColorBrush(Colors.Red);
                }

            }));

        }

        public void ExperimentFinished(string dummy)
        {
            // Reset everything so we can start the next one.
            lblLastParticipant.Content = edParticipantID.Text;
            edParticipantID.Text = "";
            cbYoungParticipant.IsChecked = false;
        }

        private void ConnectToSocket()
        {
            // Keep trying to connect to the socket until it works
            this.socket = new SocketConnection(this.MessageReceived, this.ConnectToSocket);

            this.connecting = true;

            while (this.connecting)
            {
                try
                {
                    this.socket.Connect("controlpanel", "127.0.0.1", 1336);
                    this.connecting = false;
                }

                catch (Exception e)
                {
                    Thread.Sleep(1000);
                }
            }

        }

        void MainWindow_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            // @TODO: send exit command to the main_game and Kinect tool
        }

        private void Button_Click_1(object sender, RoutedEventArgs e)
        {
            this.socket.Send("start_game(" + edParticipantID.Text + "," + cbYoungParticipant.IsChecked + ")");
        }

        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            try
            {
                this.socket.Send("exit()");
            }

            catch (Exception ex) {

            }
            
        }

        private void btnStopRecording_Click(object sender, RoutedEventArgs e)
        {
            // This is implemented in case the Kinect fails to detect the end of a recording automatically.
            this.socket.Send("StopRecording()", "kinectrecorder");
        }
    }
}
