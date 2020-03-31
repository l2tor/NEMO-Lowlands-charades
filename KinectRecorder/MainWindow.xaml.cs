//------------------------------------------------------------------------------
// <copyright file="MainWindow.xaml.cs" company="Microsoft">
//     Copyright (c) Microsoft Corporation.  All rights reserved.
// </copyright>
//------------------------------------------------------------------------------

namespace Microsoft.Samples.Kinect.BodyBasics
{
    using System;
    using System.Collections.Generic;
    using System.ComponentModel;
    using System.Diagnostics;
    using System.Globalization;
    using System.IO;
    using System.Windows;
    using System.Windows.Media;
    using System.Windows.Media.Imaging;
    using Microsoft.Kinect;
    using Microsoft.Kinect.Face; 
    using System.Net.Sockets;
    using System.Web.Script.Serialization;
    using System.Windows.Controls;
    using Emgu.CV;
    using Emgu.CV.Structure;
    using System.Threading;
    using System.Runtime.InteropServices;
    using System.Collections.Concurrent;
    using NAudio.CoreAudioApi;
    using NAudio.Wave;
    using GestureShared;
    using System.Reflection;

    /// <summary>
    /// Interaction logic for MainWindow
    /// </summary>
    public partial class MainWindow : Window, INotifyPropertyChanged
    {
        /// <summary>
        /// Radius of drawn hand circles
        /// </summary>
        private const double HandSize = 30;

        /// <summary>
        /// Thickness of drawn joint lines
        /// </summary>
        private const double JointThickness = 3;

        /// <summary>
        /// Thickness of clip edge rectangles
        /// </summary>
        private const double ClipBoundsThickness = 10;

        /// <summary>
        /// Constant for clamping Z values of camera space points from being negative
        /// </summary>
        private const float InferredZPositionClamp = 0.1f;

        /// <summary>
        /// Brush used for drawing hands that are currently tracked as closed
        /// </summary>
        private readonly Brush handClosedBrush = new SolidColorBrush(Color.FromArgb(128, 255, 0, 0));

        /// <summary>
        /// Brush used for drawing hands that are currently tracked as opened
        /// </summary>
        private readonly Brush handOpenBrush = new SolidColorBrush(Color.FromArgb(128, 0, 255, 0));

        /// <summary>
        /// Brush used for drawing hands that are currently tracked as in lasso (pointer) position
        /// </summary>
        private readonly Brush handLassoBrush = new SolidColorBrush(Color.FromArgb(128, 0, 0, 255));

        /// <summary>
        /// Brush used for drawing joints that are currently tracked
        /// </summary>
        private readonly Brush trackedJointBrush = new SolidColorBrush(Color.FromArgb(255, 68, 192, 68));

        /// <summary>
        /// Brush used for drawing joints that are currently inferred
        /// </summary>        
        private readonly Brush inferredJointBrush = Brushes.Yellow;

        /// <summary>
        /// Pen used for drawing bones that are currently inferred
        /// </summary>        
        private readonly Pen inferredBonePen = new Pen(Brushes.Gray, 1);

        /// <summary>
        /// Drawing group for body rendering output
        /// </summary>
        private DrawingGroup drawingGroup;

        /// <summary>
        /// Drawing image that we will display
        /// </summary>
        private DrawingImage imageSource;

        /// <summary>
        /// Active Kinect sensor
        /// </summary>
        private KinectSensor kinectSensor = null;

        /// <summary>
        /// Coordinate mapper to map one type of point to another
        /// </summary>
        private CoordinateMapper coordinateMapper = null;

        /// <summary>
        /// Reader for body frames
        /// </summary>
        private BodyFrameReader bodyFrameReader = null;

        /// <summary>
        /// Array for the bodies
        /// </summary>
        private Body[] bodies = null;

        /// <summary>
        /// Number of bodies tracked
        /// </summary>
        private int bodyCount;

        /// <summary>
        /// definition of bones
        /// </summary>
        private List<Tuple<JointType, JointType>> bones;

        /// <summary>
        /// Face frame sources
        /// </summary>
        private FaceFrameSource[] faceFrameSources = null;

        /// <summary>
        /// Face frame readers
        /// </summary>
        private FaceFrameReader[] faceFrameReaders = null;

        /// <summary>
        /// Storage for face frame results
        /// </summary>
        private FaceFrameResult[] faceFrameResults = null;

        /// <summary>
        /// Face rotation display angle increment in degrees
        /// </summary>
        private const double FaceRotationIncrementInDegrees = 5.0;

        /// <summary>
        /// Width of display (depth space)
        /// </summary>
        private int displayWidth;

        /// <summary>
        /// Height of display (depth space)
        /// </summary>
        private int displayHeight;

        /// <summary>
        /// List of colors for each body tracked
        /// </summary>
        private List<Pen> bodyColors;

        /// <summary>
        /// Current status text to display
        /// </summary>
        private string statusText = null;

        /// <summary>
        /// Reader for color frames
        /// </summary>
        private ColorFrameReader colorFrameReader = null;

        /// <summary>
        /// Bitmap to display
        /// </summary>
        private WriteableBitmap colorBitmap = null;

        private Joint prevLeftHand = new Joint();
        private Joint prevRightHand = new Joint();
        private DateTime lastMeasured = DateTime.MaxValue;
        private double totalRestTime = 0;
        private double totalActivityTime = 0;

        private SocketConnection socket;

        private bool isRecording = false;
        private String csvOut = null;
        private String filenameBase = "";
        private String concept = "";

        private VideoWriter videoWriter = null;
        private VideoWriter skelWriter = null;

        private byte[] imgBuffer = new byte[8294400];

        // P/Invoke declarations
        private delegate void TimerEventHandler(int id, int msg, IntPtr user, int dw1, int dw2);

        private const int TIME_PERIODIC = 1;
        private const int EVENT_TYPE = TIME_PERIODIC;// + 0x100;  // TIME_KILL_SYNCHRONOUS causes a hang ?!
        [DllImport("winmm.dll")]
        private static extern int timeSetEvent(int delay, int resolution,
                                                TimerEventHandler handler, IntPtr user, int eventType);
        [DllImport("winmm.dll")]
        private static extern int timeKillEvent(int id);
        [DllImport("winmm.dll")]
        private static extern int timeBeginPeriod(int msec);
        [DllImport("winmm.dll")]
        private static extern int timeEndPeriod(int msec);

        private int mTimerId;
        private TimerEventHandler mHandler;
        private int mTestTick;
        private DateTime mTestStart;

        private int mTimerIdskel;
        private TimerEventHandler mHandlerskel;
        private int mTestTickskel;
        private DateTime mTestStartskel;

        private DateTime startTime = DateTime.MinValue;

        // Stuff for recording audio
        private IWaveIn waveIn;
        private WaveFileWriter writer;

        private string participantID;
        private bool isYoungParticipant;

        private bool connecting = true;

        private bool hourglassSent = false;


        /// <summary>
        /// Initializes a new instance of the MainWindow class.
        /// </summary>
        public MainWindow()
        {
            // one sensor is currently supported
            this.kinectSensor = KinectSensor.GetDefault();

            // get the coordinate mapper
            this.coordinateMapper = this.kinectSensor.CoordinateMapper;

            // get the depth (display) extents
            FrameDescription frameDescription = this.kinectSensor.DepthFrameSource.FrameDescription;

            // get size of joint space
            this.displayWidth = frameDescription.Width;
            this.displayHeight = frameDescription.Height;

            // open the reader for the body frames
            this.bodyFrameReader = this.kinectSensor.BodyFrameSource.OpenReader();

            // a bone defined as a line between two joints
            this.bones = new List<Tuple<JointType, JointType>>();

            // Torso
            this.bones.Add(new Tuple<JointType, JointType>(JointType.Head, JointType.Neck));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.Neck, JointType.SpineShoulder));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineShoulder, JointType.SpineMid));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineMid, JointType.SpineBase));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineShoulder, JointType.ShoulderRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineShoulder, JointType.ShoulderLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineBase, JointType.HipRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineBase, JointType.HipLeft));

            // Right Arm
            this.bones.Add(new Tuple<JointType, JointType>(JointType.ShoulderRight, JointType.ElbowRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.ElbowRight, JointType.WristRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.WristRight, JointType.HandRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.HandRight, JointType.HandTipRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.WristRight, JointType.ThumbRight));

            // Left Arm
            this.bones.Add(new Tuple<JointType, JointType>(JointType.ShoulderLeft, JointType.ElbowLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.ElbowLeft, JointType.WristLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.WristLeft, JointType.HandLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.HandLeft, JointType.HandTipLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.WristLeft, JointType.ThumbLeft));

            // Right Leg
            this.bones.Add(new Tuple<JointType, JointType>(JointType.HipRight, JointType.KneeRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.KneeRight, JointType.AnkleRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.AnkleRight, JointType.FootRight));

            // Left Leg
            this.bones.Add(new Tuple<JointType, JointType>(JointType.HipLeft, JointType.KneeLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.KneeLeft, JointType.AnkleLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.AnkleLeft, JointType.FootLeft));

            // populate body colors, one for each BodyIndex
            this.bodyColors = new List<Pen>();

            this.bodyColors.Add(new Pen(Brushes.Red, 6));
            this.bodyColors.Add(new Pen(Brushes.Orange, 6));
            this.bodyColors.Add(new Pen(Brushes.Green, 6));
            this.bodyColors.Add(new Pen(Brushes.Blue, 6));
            this.bodyColors.Add(new Pen(Brushes.Indigo, 6));
            this.bodyColors.Add(new Pen(Brushes.Violet, 6));

            // open the reader for the color frames
            this.colorFrameReader = this.kinectSensor.ColorFrameSource.OpenReader();

            // wire handler for frame arrival
            this.colorFrameReader.FrameArrived += this.Reader_ColorFrameArrived;

            // create the colorFrameDescription from the ColorFrameSource using Bgra format
            FrameDescription colorFrameDescription = this.kinectSensor.ColorFrameSource.CreateFrameDescription(ColorImageFormat.Bgra);

            // create the bitmap to display
            this.colorBitmap = new WriteableBitmap(colorFrameDescription.Width, colorFrameDescription.Height, 96.0, 96.0, PixelFormats.Bgr32, null);


            // set the maximum number of bodies that would be tracked by Kinect
            this.bodyCount = this.kinectSensor.BodyFrameSource.BodyCount;

            // allocate storage to store body objects
            this.bodies = new Body[this.bodyCount];

            // specify the required face frame results
            /*FaceFrameFeatures faceFrameFeatures =
                FaceFrameFeatures.BoundingBoxInColorSpace
                | FaceFrameFeatures.PointsInColorSpace
                | FaceFrameFeatures.RotationOrientation
                | FaceFrameFeatures.FaceEngagement
                | FaceFrameFeatures.Glasses
                | FaceFrameFeatures.Happy
                | FaceFrameFeatures.LeftEyeClosed
                | FaceFrameFeatures.RightEyeClosed
                | FaceFrameFeatures.LookingAway
                | FaceFrameFeatures.MouthMoved
                | FaceFrameFeatures.MouthOpen;*/

            FaceFrameFeatures faceFrameFeatures = FaceFrameFeatures.RotationOrientation;

            // create a face frame source + reader to track each face in the FOV
            this.faceFrameSources = new FaceFrameSource[this.bodyCount];
            this.faceFrameReaders = new FaceFrameReader[this.bodyCount];
            for (int i = 0; i < this.bodyCount; i++)
            {
                // create the face frame source with the required face frame features and an initial tracking Id of 0
                this.faceFrameSources[i] = new FaceFrameSource(this.kinectSensor, 0, faceFrameFeatures);

                // open the corresponding reader
                this.faceFrameReaders[i] = this.faceFrameSources[i].OpenReader();
            }

            // allocate storage to store face frame results for each face in the FOV
            this.faceFrameResults = new FaceFrameResult[this.bodyCount];


            // set IsAvailableChanged event notifier
            this.kinectSensor.IsAvailableChanged += this.Sensor_IsAvailableChanged;

            // open the sensor
            this.kinectSensor.Open();

            // set the status text
            this.StatusText = this.kinectSensor.IsAvailable ? Properties.Resources.RunningStatusText
                                                            : Properties.Resources.NoSensorStatusText;

            // Create the drawing group we'll use for drawing
            this.drawingGroup = new DrawingGroup();

            // Create an image source that we can use in our image control
            this.imageSource = new DrawingImage(this.drawingGroup);

            // use the window object as the view model in this simple example
            this.DataContext = this;

            // Connect to the main game
            this.ConnectToSocket();

            // initialize the components (controls) of the window
            this.InitializeComponent();
        }

        private void MessageReceived(string sender, string content)
        {
            Console.WriteLine(sender + ": " + content);
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

        private void ConnectToSocket()
        {
            // Keep trying to connect to the socket connection with the main game
            this.socket = new SocketConnection(this.MessageReceived, this.ConnectToSocket);
            this.connecting = true;

            while (this.connecting)
            {
                try
                {
                    this.socket.Connect("kinectrecorder", "127.0.0.1", 1336);
                    this.connecting = false;
                }

                catch (Exception e)
                {
                    Thread.Sleep(1000);
                }

            }
        }


        private void FinalizeWaveFile()
        {
            if (this.writer != null)
            {
                this.writer.Dispose();
                this.writer = null;
            }
        }

        void OnWaveDataAvailable(object sender, WaveInEventArgs e)
        {
            this.writer.Write(e.Buffer, 0, e.BytesRecorded);
        }

        /// <summary>
        /// INotifyPropertyChangedPropertyChanged event to allow window controls to bind to changeable data
        /// </summary>
        public event PropertyChangedEventHandler PropertyChanged;

        /// <summary>
        /// Gets the bitmap to display
        /// </summary>
        public ImageSource ImageSource
        {
            get
            {
                return this.imageSource;
            }
        }

        /// <summary>
        /// Gets or sets the current status text to display
        /// </summary>
        public string StatusText
        {
            get
            {
                return this.statusText;
            }

            set
            {
                if (this.statusText != value)
                {
                    this.statusText = value;

                    // notify any bound elements that the text has changed
                    if (this.PropertyChanged != null)
                    {
                        this.PropertyChanged(this, new PropertyChangedEventArgs("StatusText"));
                    }
                }
            }
        }

        /// <summary>
        /// Execute start up tasks
        /// </summary>
        /// <param name="sender">object sending the event</param>
        /// <param name="e">event arguments</param>
        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            for (int i = 0; i < this.bodyCount; i++)
            {
                if (this.faceFrameReaders[i] != null)
                {
                    // wire handler for face frame arrival
                    this.faceFrameReaders[i].FrameArrived += this.Reader_FaceFrameArrived;
                }
            }

            if (this.bodyFrameReader != null)
            {
                this.bodyFrameReader.FrameArrived += this.Reader_FrameArrived;
            }
        }

        /// <summary>
        /// Execute shutdown tasks
        /// </summary>
        /// <param name="sender">object sending the event</param>
        /// <param name="e">event arguments</param>
        private void MainWindow_Closing(object sender, CancelEventArgs e)
        {
            StopRecording();

            for (int i = 0; i < this.bodyCount; i++)
            {
                if (this.faceFrameReaders[i] != null)
                {
                    // FaceFrameReader is IDisposable
                    this.faceFrameReaders[i].Dispose();
                    this.faceFrameReaders[i] = null;
                }

                if (this.faceFrameSources[i] != null)
                {
                    // FaceFrameSource is IDisposable
                    this.faceFrameSources[i].Dispose();
                    this.faceFrameSources[i] = null;
                }
            }

            if (this.bodyFrameReader != null)
            {
                // BodyFrameReader is IDisposable
                this.bodyFrameReader.Dispose();
                this.bodyFrameReader = null;
            }

            if (this.kinectSensor != null)
            {
                this.kinectSensor.Close();
                this.kinectSensor = null;
            }
        }

        /// <summary>
        /// Handles the color frame data arriving from the sensor
        /// </summary>
        /// <param name="sender">object sending the event</param>
        /// <param name="e">event arguments</param>
        private void Reader_ColorFrameArrived(object sender, ColorFrameArrivedEventArgs e)
        {
            // ColorFrame is IDisposable
            using (ColorFrame colorFrame = e.FrameReference.AcquireFrame())
            {

                if (colorFrame != null)
                {
                    double fps = 1.0 / colorFrame.ColorCameraSettings.FrameInterval.TotalSeconds;

                    if (this.isRecording)
                    {
                        this.colorBitmap.Lock();
                        FrameDescription colorFrameDescription = colorFrame.FrameDescription;

                        byte[] tmp = new byte[colorFrameDescription.Width * colorFrameDescription.Height * 4];
                        colorFrame.CopyConvertedFrameDataToArray(tmp, ColorImageFormat.Bgra);

                        this.colorBitmap.Unlock();

                        //lock (this.imgBuffer)
                        //{
                            this.imgBuffer = tmp;
                        //}
                    }
                }
            }
        }

        private void SaveFrame(int id, int msg, IntPtr user, int dw1, int dw2)
        {
            if (this.startTime == DateTime.MinValue)
                this.startTime = DateTime.Now;

            //lock (this.imgBuffer)
            //{
                Image<Bgra, Byte> tmp = new Image<Bgra, Byte>(1920, 1080);
                tmp.Bytes = this.imgBuffer;
                Image<Bgr, Byte> tmp2 = tmp.Convert<Bgr, Byte>();
                tmp2 = tmp2.Resize(0.5, Emgu.CV.CvEnum.INTER.CV_INTER_LINEAR);

                this.videoWriter.WriteFrame<Bgr, Byte>(tmp2);
            //}
        }

        private void SaveSkeleton(int id, int msg, IntPtr user, int dw1, int dw2)
        {
            // This creates the "skeleton video"
            try
            {
                Application.Current.Dispatcher.Invoke(() =>
                {

                    RenderTargetBitmap skelrbmp = new RenderTargetBitmap((int)imgSkeleton.ActualWidth, (int)imgSkeleton.ActualHeight, 96, 96, PixelFormats.Pbgra32);
                    skelrbmp.Render(imgSkeleton);
                    System.Drawing.Bitmap skelbmp;

                    using (MemoryStream outStream = new MemoryStream())
                    {
                        BitmapEncoder enc = new BmpBitmapEncoder();
                        enc.Frames.Add(BitmapFrame.Create(skelrbmp));
                        enc.Save(outStream);
                        skelbmp = new System.Drawing.Bitmap(outStream);
                    }

                    if (this.isRecording)
                    {
                        this.skelWriter.WriteFrame<Bgr, Byte>(new Image<Bgr, Byte>(skelbmp));
                    }
                });

            }
            
            catch (Exception ex)
            {

            }
        }

        /// <summary>
        /// Returns the index of the face frame source
        /// </summary>
        /// <param name="faceFrameSource">the face frame source</param>
        /// <returns>the index of the face source in the face source array</returns>
        private int GetFaceSourceIndex(FaceFrameSource faceFrameSource)
        {
            int index = -1;

            for (int i = 0; i < this.bodyCount; i++)
            {
                if (this.faceFrameSources[i] == faceFrameSource)
                {
                    index = i;
                    break;
                }
            }

            return index;
        }

        /// <summary>
        /// Handles the face frame data arriving from the sensor
        /// </summary>
        /// <param name="sender">object sending the event</param>
        /// <param name="e">event arguments</param>
        private void Reader_FaceFrameArrived(object sender, FaceFrameArrivedEventArgs e)
        {
            using (FaceFrame faceFrame = e.FrameReference.AcquireFrame())
            {
                if (faceFrame != null)
                {
                    // get the index of the face source from the face source array
                    int index = this.GetFaceSourceIndex(faceFrame.FaceFrameSource);

                    this.faceFrameResults[index] = faceFrame.FaceFrameResult;
                }
            }
        }

        /// <summary>
        /// Converts rotation quaternion to Euler angles 
        /// And then maps them to a specified range of values to control the refresh rate
        /// </summary>
        /// <param name="rotQuaternion">face rotation quaternion</param>
        /// <param name="pitch">rotation about the X-axis</param>
        /// <param name="yaw">rotation about the Y-axis</param>
        /// <param name="roll">rotation about the Z-axis</param>
        private static void ExtractFaceRotationInDegrees(Vector4 rotQuaternion, out int pitch, out int yaw, out int roll)
        {
            double x = rotQuaternion.X;
            double y = rotQuaternion.Y;
            double z = rotQuaternion.Z;
            double w = rotQuaternion.W;

            // convert face rotation quaternion to Euler angles in degrees
            double yawD, pitchD, rollD;
            pitchD = Math.Atan2(2 * ((y * z) + (w * x)), (w * w) - (x * x) - (y * y) + (z * z)) / Math.PI * 180.0;
            yawD = Math.Asin(2 * ((w * y) - (x * z))) / Math.PI * 180.0;
            rollD = Math.Atan2(2 * ((x * y) + (w * z)), (w * w) + (x * x) - (y * y) - (z * z)) / Math.PI * 180.0;

            // clamp the values to a multiple of the specified increment to control the refresh rate
            double increment = FaceRotationIncrementInDegrees;
            pitch = (int)(Math.Floor((pitchD + ((increment / 2.0) * (pitchD > 0 ? 1.0 : -1.0))) / increment) * increment);
            yaw = (int)(Math.Floor((yawD + ((increment / 2.0) * (yawD > 0 ? 1.0 : -1.0))) / increment) * increment);
            roll = (int)(Math.Floor((rollD + ((increment / 2.0) * (rollD > 0 ? 1.0 : -1.0))) / increment) * increment);
        }


        /// <summary>
        /// Handles the body frame data arriving from the sensor
        /// </summary>
        /// <param name="sender">object sending the event</param>
        /// <param name="e">event arguments</param>
        private void Reader_FrameArrived(object sender, BodyFrameArrivedEventArgs e)
        {
            //if (!isRecording)
            //    return;

            bool dataReceived = false;

            using (BodyFrame bodyFrame = e.FrameReference.AcquireFrame())
            {
                if (bodyFrame != null)
                {
                    if (this.bodies == null)
                    {
                        this.bodies = new Body[bodyFrame.BodyCount];
                    }

                    // The first time GetAndRefreshBodyData is called, Kinect will allocate each Body in the array.
                    // As long as those body objects are not disposed and not set to null in the array,
                    // those body objects will be re-used.
                    bodyFrame.GetAndRefreshBodyData(this.bodies);
                    dataReceived = true;
                }
            }

            if (dataReceived)
            {
                using (DrawingContext dc = this.drawingGroup.Open())
                {
                    // Draw a transparent background to set the render size
                    dc.DrawRectangle(Brushes.Black, null, new Rect(0.0, 0.0, this.displayWidth, this.displayHeight));

                    int penIndex = 0;
                    for (int i = 0; i < this.bodyCount; i++)
                    {
                        Body body = this.bodies[i];
                        Pen drawPen = this.bodyColors[penIndex++];

                        if (body.IsTracked)
                        {
                            this.DrawClippedEdges(body, dc);

                            TimeSpan timediff = DateTime.Now - this.startTime;
                            double secs = timediff.TotalMilliseconds / 1000;

                            IReadOnlyDictionary<JointType, Joint> joints = body.Joints;
                            IReadOnlyDictionary<JointType, JointOrientation> orientations = body.JointOrientations;


                            if (this.isRecording)
                            {
                                // Face stuff
                                int face_pitch = 0;
                                int face_yaw = 0;
                                int face_roll = 0;

                                if (this.faceFrameSources[i].IsTrackingIdValid)
                                {
                                    FaceFrameResult ffres = this.faceFrameResults[i];
                                    if (ffres != null && ffres.FaceRotationQuaternion != null)
                                    {
                                        ExtractFaceRotationInDegrees(ffres.FaceRotationQuaternion, out face_pitch, out face_yaw, out face_roll);
                                    }

                                }
                                else
                                {
                                    if (this.bodies[i].IsTracked)
                                    {
                                        // update the face frame source to track this body
                                        this.faceFrameSources[i].TrackingId = this.bodies[i].TrackingId;
                                    }
                                }

                                // Check if there is still movement, otherwise automatically cut the recording here                                
                                DateTime now = DateTime.Now;
                                double diff = (now - lastMeasured).TotalMilliseconds;
                                if (diff >= 500)
                                {
                                    this.lastMeasured = now;
                                    float dl = joints[JointType.HandLeft].Position.X - prevLeftHand.Position.X + joints[JointType.HandLeft].Position.Y - prevLeftHand.Position.Y + joints[JointType.HandLeft].Position.Z - prevLeftHand.Position.Z;
                                    Console.WriteLine(dl.ToString());
                                    float dr = joints[JointType.HandRight].Position.X - prevRightHand.Position.X + joints[JointType.HandRight].Position.Y - prevRightHand.Position.Y + joints[JointType.HandRight].Position.Z - prevRightHand.Position.Z;
                                    this.prevLeftHand = joints[JointType.HandLeft];
                                    this.prevRightHand = joints[JointType.HandRight];
                                    
                                    if (dl < 0.01 && dr < 0.01) // If both hands moved less than .01 meters in the last 500 milliseconds...
                                    {
                                        this.totalRestTime += diff;

                                        // We make sure that at least there is some motion recorded
                                        if (this.totalActivityTime >= 2000 && this.totalRestTime >= 500 && !this.hourglassSent)
                                        {
                                            // Show the hourglass, indicating that we are about to cut off the recording
                                            this.hourglassSent = true;
                                            this.socket.Send("show_hourglass()", "webclient");
                                        }
                                    }

                                    else
                                    {
                                        this.totalActivityTime += diff;
                                        this.totalRestTime = 0;
                                    }

                                    if (this.totalRestTime >= 1500 && this.totalActivityTime >= 2000)
                                    {
                                        Console.WriteLine("=== INACTIVITY DETECTED -> DONE RECORDING ==="); // Finish recording
                                        this.StopRecording();
                                        return;
                                    }
                                }


                                string outstr = secs + ",";
                                outstr += joints[JointType.Head].Position.X + "," + joints[JointType.Head].Position.Y + "," + joints[JointType.Head].Position.Z + ",";
                                outstr += joints[JointType.Neck].Position.X + "," + joints[JointType.Neck].Position.Y + "," + joints[JointType.Neck].Position.Z + ",";
                                outstr += joints[JointType.ShoulderRight].Position.X + "," + joints[JointType.ShoulderRight].Position.Y + "," + joints[JointType.ShoulderRight].Position.Z + ",";
                                outstr += joints[JointType.ElbowRight].Position.X + "," + joints[JointType.ElbowRight].Position.Y + "," + joints[JointType.ElbowRight].Position.Z + ",";
                                outstr += joints[JointType.WristRight].Position.X + "," + joints[JointType.WristRight].Position.Y + "," + joints[JointType.WristRight].Position.Z + ",";
                                outstr += joints[JointType.ShoulderLeft].Position.X + "," + joints[JointType.ShoulderLeft].Position.Y + "," + joints[JointType.ShoulderLeft].Position.Z + ",";
                                outstr += joints[JointType.ElbowLeft].Position.X + "," + joints[JointType.ElbowLeft].Position.Y + "," + joints[JointType.ElbowLeft].Position.Z + ",";
                                outstr += joints[JointType.WristLeft].Position.X + "," + joints[JointType.WristLeft].Position.Y + "," + joints[JointType.WristLeft].Position.Z + ",";
                                outstr += joints[JointType.HipRight].Position.X + "," + joints[JointType.HipRight].Position.Y + "," + joints[JointType.HipRight].Position.Z + ",";
                                outstr += joints[JointType.KneeRight].Position.X + "," + joints[JointType.KneeRight].Position.Y + "," + joints[JointType.KneeRight].Position.Z + ",";
                                outstr += joints[JointType.AnkleRight].Position.X + "," + joints[JointType.AnkleRight].Position.Y + "," + joints[JointType.AnkleRight].Position.Z + ",";
                                outstr += joints[JointType.HipLeft].Position.X + "," + joints[JointType.HipLeft].Position.Y + "," + joints[JointType.HipLeft].Position.Z + ",";
                                outstr += joints[JointType.KneeLeft].Position.X + "," + joints[JointType.KneeLeft].Position.Y + "," + joints[JointType.KneeLeft].Position.Z + ",";
                                outstr += joints[JointType.AnkleLeft].Position.X + "," + joints[JointType.AnkleLeft].Position.Y + "," + joints[JointType.AnkleLeft].Position.Z + ",";
                                outstr += joints[JointType.FootRight].Position.X + "," + joints[JointType.FootRight].Position.Y + "," + joints[JointType.FootRight].Position.Z + ",";
                                outstr += joints[JointType.FootLeft].Position.X + "," + joints[JointType.FootLeft].Position.Y + "," + joints[JointType.FootLeft].Position.Z + ",";
                                outstr += joints[JointType.HandRight].Position.X + "," + joints[JointType.HandRight].Position.Y + "," + joints[JointType.HandRight].Position.Z + ",";
                                outstr += joints[JointType.HandLeft].Position.X + "," + joints[JointType.HandLeft].Position.Y + "," + joints[JointType.HandLeft].Position.Z + ",";
                                outstr += joints[JointType.HandTipRight].Position.X + "," + joints[JointType.HandTipRight].Position.Y + "," + joints[JointType.HandTipRight].Position.Z + ",";
                                outstr += joints[JointType.HandTipLeft].Position.X + "," + joints[JointType.HandTipLeft].Position.Y + "," + joints[JointType.HandTipLeft].Position.Z + ",";
                                outstr += joints[JointType.SpineBase].Position.X + "," + joints[JointType.SpineBase].Position.Y + "," + joints[JointType.SpineBase].Position.Z + ",";
                                outstr += joints[JointType.SpineMid].Position.X + "," + joints[JointType.SpineMid].Position.Y + "," + joints[JointType.SpineMid].Position.Z + ",";
                                outstr += joints[JointType.SpineShoulder].Position.X + "," + joints[JointType.SpineShoulder].Position.Y + "," + joints[JointType.SpineShoulder].Position.Z + ",";

                                if (body.HandRightState == HandState.Closed)
                                    outstr += "0,";
                                else if (body.HandRightState == HandState.Open || body.HandRightState == HandState.Lasso)
                                    outstr += "1,";
                                else
                                    outstr += "-1,";

                                if (body.HandLeftState == HandState.Closed)
                                    outstr += "0,";
                                else if (body.HandLeftState == HandState.Open || body.HandLeftState == HandState.Lasso)
                                    outstr += "1,";
                                else
                                    outstr += "-1,";

                                outstr += body.HandRightConfidence + ",";
                                outstr += body.HandLeftConfidence + ",";

                                outstr += joints[JointType.ThumbRight].Position.X + "," + joints[JointType.ThumbRight].Position.Y + "," + joints[JointType.ThumbRight].Position.Z + ",";
                                outstr += joints[JointType.ThumbLeft].Position.X + "," + joints[JointType.ThumbLeft].Position.Y + "," + joints[JointType.ThumbLeft].Position.Z + ",";


                                // And now for joint angles..
                                // End joints don't seem to have angles, so we leave those out
                                // Some information on how this might be useful to calculate various yaw/pitch/roll values:
                                // https://social.msdn.microsoft.com/Forums/en-US/245a3a09-a2e4-4e0e-8c12-b8625102376a/kinect-v2-sdk-joint-orientation?forum=kinectv2sdk
                                //outstr += orientations[JointType.Head].Orientation.X + "," + orientations[JointType.Head].Orientation.Y + "," + orientations[JointType.Head].Orientation.Z + "," + orientations[JointType.Head].Orientation.W + ",";
                                outstr += orientations[JointType.Neck].Orientation.X + "," + orientations[JointType.Neck].Orientation.Y + "," + orientations[JointType.Neck].Orientation.Z + "," + orientations[JointType.Neck].Orientation.W + ",";
                                outstr += orientations[JointType.ShoulderRight].Orientation.X + "," + orientations[JointType.ShoulderRight].Orientation.Y + "," + orientations[JointType.ShoulderRight].Orientation.Z + "," + orientations[JointType.ShoulderRight].Orientation.W + ",";
                                outstr += orientations[JointType.ElbowRight].Orientation.X + "," + orientations[JointType.ElbowRight].Orientation.Y + "," + orientations[JointType.ElbowRight].Orientation.Z + "," + orientations[JointType.ElbowRight].Orientation.W + ",";
                                outstr += orientations[JointType.WristRight].Orientation.X + "," + orientations[JointType.WristRight].Orientation.Y + "," + orientations[JointType.WristRight].Orientation.Z + "," + orientations[JointType.WristRight].Orientation.W + ",";
                                outstr += orientations[JointType.ShoulderLeft].Orientation.X + "," + orientations[JointType.ShoulderLeft].Orientation.Y + "," + orientations[JointType.ShoulderLeft].Orientation.Z + "," + orientations[JointType.ShoulderLeft].Orientation.W + ",";
                                outstr += orientations[JointType.ElbowLeft].Orientation.X + "," + orientations[JointType.ElbowLeft].Orientation.Y + "," + orientations[JointType.ElbowLeft].Orientation.Z + "," + orientations[JointType.ElbowLeft].Orientation.W + ",";
                                outstr += orientations[JointType.WristLeft].Orientation.X + "," + orientations[JointType.WristLeft].Orientation.Y + "," + orientations[JointType.WristLeft].Orientation.Z + "," + orientations[JointType.WristLeft].Orientation.W + ",";
                                outstr += orientations[JointType.HipRight].Orientation.X + "," + orientations[JointType.HipRight].Orientation.Y + "," + orientations[JointType.HipRight].Orientation.Z + "," + orientations[JointType.HipRight].Orientation.W + ",";
                                outstr += orientations[JointType.KneeRight].Orientation.X + "," + orientations[JointType.KneeRight].Orientation.Y + "," + orientations[JointType.KneeRight].Orientation.Z + "," + orientations[JointType.KneeRight].Orientation.W + ",";
                                outstr += orientations[JointType.AnkleRight].Orientation.X + "," + orientations[JointType.AnkleRight].Orientation.Y + "," + orientations[JointType.AnkleRight].Orientation.Z + "," + orientations[JointType.AnkleRight].Orientation.W + ",";
                                outstr += orientations[JointType.HipLeft].Orientation.X + "," + orientations[JointType.HipLeft].Orientation.Y + "," + orientations[JointType.HipLeft].Orientation.Z + "," + orientations[JointType.HipLeft].Orientation.W + ",";
                                outstr += orientations[JointType.KneeLeft].Orientation.X + "," + orientations[JointType.KneeLeft].Orientation.Y + "," + orientations[JointType.KneeLeft].Orientation.Z + "," + orientations[JointType.KneeLeft].Orientation.W + ",";
                                outstr += orientations[JointType.AnkleLeft].Orientation.X + "," + orientations[JointType.AnkleLeft].Orientation.Y + "," + orientations[JointType.AnkleLeft].Orientation.Z + "," + orientations[JointType.AnkleLeft].Orientation.W + ",";
                                //outstr += orientations[JointType.FootRight].Orientation.X + "," + orientations[JointType.FootRight].Orientation.Y + "," + orientations[JointType.FootRight].Orientation.Z + "," + orientations[JointType.FootRight].Orientation.W + ",";
                                //outstr += orientations[JointType.FootLeft].Orientation.X + "," + orientations[JointType.FootLeft].Orientation.Y + "," + orientations[JointType.FootLeft].Orientation.Z + "," + orientations[JointType.FootLeft].Orientation.W + ",";
                                outstr += orientations[JointType.HandRight].Orientation.X + "," + orientations[JointType.HandRight].Orientation.Y + "," + orientations[JointType.HandRight].Orientation.Z + "," + orientations[JointType.HandRight].Orientation.W + ",";
                                outstr += orientations[JointType.HandLeft].Orientation.X + "," + orientations[JointType.HandLeft].Orientation.Y + "," + orientations[JointType.HandLeft].Orientation.Z + "," + orientations[JointType.HandLeft].Orientation.W + ",";
                                //outstr += orientations[JointType.HandTipRight].Orientation.X + "," + orientations[JointType.HandTipRight].Orientation.Y + "," + orientations[JointType.HandTipRight].Orientation.Z + "," + orientations[JointType.HandTipRight].Orientation.W + ",";
                                //outstr += orientations[JointType.HandTipLeft].Orientation.X + "," + orientations[JointType.HandTipLeft].Orientation.Y + "," + orientations[JointType.HandTipLeft].Orientation.Z + "," + orientations[JointType.HandTipLeft].Orientation.W + ",";
                                outstr += orientations[JointType.SpineBase].Orientation.X + "," + orientations[JointType.SpineBase].Orientation.Y + "," + orientations[JointType.SpineBase].Orientation.Z + "," + orientations[JointType.SpineBase].Orientation.W + ",";
                                outstr += orientations[JointType.SpineMid].Orientation.X + "," + orientations[JointType.SpineMid].Orientation.Y + "," + orientations[JointType.SpineMid].Orientation.Z + "," + orientations[JointType.SpineMid].Orientation.W + ",";
                                outstr += orientations[JointType.SpineShoulder].Orientation.X + "," + orientations[JointType.SpineShoulder].Orientation.Y + "," + orientations[JointType.SpineShoulder].Orientation.Z + "," + orientations[JointType.SpineShoulder].Orientation.W + ",";
                                //outstr += orientations[JointType.ThumbRight].Orientation.X + "," + orientations[JointType.ThumbRight].Orientation.Y + "," + orientations[JointType.ThumbRight].Orientation.Z + "," + orientations[JointType.ThumbRight].Orientation.W + ",";
                                //outstr += orientations[JointType.ThumbLeft].Orientation.X + "," + orientations[JointType.ThumbLeft].Orientation.Y + "," + orientations[JointType.ThumbLeft].Orientation.Z + "," + orientations[JointType.ThumbLeft].Orientation.W + ",";
                                outstr += face_pitch + "," + face_yaw + "," + face_roll;
                                //outstr += "test";


                                outstr += "\n";


                                string stamp = timediff.TotalMilliseconds + "";//DateTime.Now.ToString("yyyyMMddHHmmssffff");
                                                                               //this.colorBitmap.Lock();
                                                                               /*FileStream fout = new FileStream("output\\" + stamp + ".png", FileMode.Create);
                                                                               PngBitmapEncoder encoder = new PngBitmapEncoder();
                                                                               encoder.Frames.Add(BitmapFrame.Create(this.colorBitmap));
                                                                               encoder.Save(fout);
                                                                               fout.Close();*/

                                //File.WriteAllText("output\\" + stamp + ".csv", outstr);
                                File.AppendAllText(this.csvOut, outstr);

                                /*List<List<float>> jointlist = new List<List<float>>();
                                string[] lines = outstr.Split('\n');

                                foreach (string l in lines)
                                {
                                    if (l != "")
                                    {
                                        List<float> joint = new List<float>();

                                        string[] coords = l.Split(',');

                                        foreach (string c in coords)
                                        {
                                            joint.Add(float.Parse(c));
                                        }

                                        jointlist.Add(joint);
                                    }
                                }

                                JointObject obj = new JointObject(jointlist);
                                JavaScriptSerializer jsonSerializer = new JavaScriptSerializer();
                                String json = jsonSerializer.Serialize(obj) + "#";
                                Byte[] data = System.Text.Encoding.ASCII.GetBytes(json);
                                this.stream.Write(data, 0, data.Length);*/
                            }

                            // convert the joint points to depth (display) space
                            Dictionary<JointType, Point> jointPoints = new Dictionary<JointType, Point>();

                            foreach (JointType jointType in joints.Keys)
                            {
                                // sometimes the depth(Z) of an inferred joint may show as negative
                                // clamp down to 0.1f to prevent coordinatemapper from returning (-Infinity, -Infinity)
                                CameraSpacePoint position = joints[jointType].Position;
                                if (position.Z < 0)
                                {
                                    position.Z = InferredZPositionClamp;
                                }

                                DepthSpacePoint depthSpacePoint = this.coordinateMapper.MapCameraPointToDepthSpace(position);
                                jointPoints[jointType] = new Point(depthSpacePoint.X, depthSpacePoint.Y);
                            }

                            this.DrawBody(joints, jointPoints, dc, drawPen);

                            this.DrawHand(body.HandLeftState, jointPoints[JointType.HandLeft], dc);
                            this.DrawHand(body.HandRightState, jointPoints[JointType.HandRight], dc);
                        }
                    }

                    // prevent drawing outside of our render area
                    this.drawingGroup.ClipGeometry = new RectangleGeometry(new Rect(0.0, 0.0, this.displayWidth, this.displayHeight));
                }
            }
        }

        /// <summary>
        /// Draws a body
        /// </summary>
        /// <param name="joints">joints to draw</param>
        /// <param name="jointPoints">translated positions of joints to draw</param>
        /// <param name="drawingContext">drawing context to draw to</param>
        /// <param name="drawingPen">specifies color to draw a specific body</param>
        private void DrawBody(IReadOnlyDictionary<JointType, Joint> joints, IDictionary<JointType, Point> jointPoints, DrawingContext drawingContext, Pen drawingPen)
        {
            // Draw the bones
            foreach (var bone in this.bones)
            {
                this.DrawBone(joints, jointPoints, bone.Item1, bone.Item2, drawingContext, drawingPen);
            }

            // Draw the joints
            foreach (JointType jointType in joints.Keys)
            {
                Brush drawBrush = null;

                TrackingState trackingState = joints[jointType].TrackingState;

                if (trackingState == TrackingState.Tracked)
                {
                    drawBrush = this.trackedJointBrush;
                }
                else if (trackingState == TrackingState.Inferred)
                {
                    drawBrush = this.inferredJointBrush;
                }

                if (drawBrush != null)
                {
                    drawingContext.DrawEllipse(drawBrush, null, jointPoints[jointType], JointThickness, JointThickness);
                }
            }
        }

        /// <summary>
        /// Draws one bone of a body (joint to joint)
        /// </summary>
        /// <param name="joints">joints to draw</param>
        /// <param name="jointPoints">translated positions of joints to draw</param>
        /// <param name="jointType0">first joint of bone to draw</param>
        /// <param name="jointType1">second joint of bone to draw</param>
        /// <param name="drawingContext">drawing context to draw to</param>
        /// /// <param name="drawingPen">specifies color to draw a specific bone</param>
        private void DrawBone(IReadOnlyDictionary<JointType, Joint> joints, IDictionary<JointType, Point> jointPoints, JointType jointType0, JointType jointType1, DrawingContext drawingContext, Pen drawingPen)
        {
            Joint joint0 = joints[jointType0];
            Joint joint1 = joints[jointType1];

            // If we can't find either of these joints, exit
            if (joint0.TrackingState == TrackingState.NotTracked ||
                joint1.TrackingState == TrackingState.NotTracked)
            {
                return;
            }

            // We assume all drawn bones are inferred unless BOTH joints are tracked
            Pen drawPen = this.inferredBonePen;
            if ((joint0.TrackingState == TrackingState.Tracked) && (joint1.TrackingState == TrackingState.Tracked))
            {
                drawPen = drawingPen;
            }

            drawingContext.DrawLine(drawPen, jointPoints[jointType0], jointPoints[jointType1]);
        }

        /// <summary>
        /// Draws a hand symbol if the hand is tracked: red circle = closed, green circle = opened; blue circle = lasso
        /// </summary>
        /// <param name="handState">state of the hand</param>
        /// <param name="handPosition">position of the hand</param>
        /// <param name="drawingContext">drawing context to draw to</param>
        private void DrawHand(HandState handState, Point handPosition, DrawingContext drawingContext)
        {
            switch (handState)
            {
                case HandState.Closed:
                    drawingContext.DrawEllipse(this.handClosedBrush, null, handPosition, HandSize, HandSize);
                    break;

                case HandState.Open:
                    drawingContext.DrawEllipse(this.handOpenBrush, null, handPosition, HandSize, HandSize);
                    break;

                case HandState.Lasso:
                    drawingContext.DrawEllipse(this.handLassoBrush, null, handPosition, HandSize, HandSize);
                    break;
            }
        }

        /// <summary>
        /// Draws indicators to show which edges are clipping body data
        /// </summary>
        /// <param name="body">body to draw clipping information for</param>
        /// <param name="drawingContext">drawing context to draw to</param>
        private void DrawClippedEdges(Body body, DrawingContext drawingContext)
        {
            FrameEdges clippedEdges = body.ClippedEdges;

            if (clippedEdges.HasFlag(FrameEdges.Bottom))
            {
                drawingContext.DrawRectangle(
                    Brushes.Red,
                    null,
                    new Rect(0, this.displayHeight - ClipBoundsThickness, this.displayWidth, ClipBoundsThickness));
            }

            if (clippedEdges.HasFlag(FrameEdges.Top))
            {
                drawingContext.DrawRectangle(
                    Brushes.Red,
                    null,
                    new Rect(0, 0, this.displayWidth, ClipBoundsThickness));
            }

            if (clippedEdges.HasFlag(FrameEdges.Left))
            {
                drawingContext.DrawRectangle(
                    Brushes.Red,
                    null,
                    new Rect(0, 0, ClipBoundsThickness, this.displayHeight));
            }

            if (clippedEdges.HasFlag(FrameEdges.Right))
            {
                drawingContext.DrawRectangle(
                    Brushes.Red,
                    null,
                    new Rect(this.displayWidth - ClipBoundsThickness, 0, ClipBoundsThickness, this.displayHeight));
            }
        }

        /// <summary>
        /// Handles the event which the sensor becomes unavailable (E.g. paused, closed, unplugged).
        /// </summary>
        /// <param name="sender">object sending the event</param>
        /// <param name="e">event arguments</param>
        private void Sensor_IsAvailableChanged(object sender, IsAvailableChangedEventArgs e)
        {
            // on failure, set the status text
            this.StatusText = this.kinectSensor.IsAvailable ? Properties.Resources.RunningStatusText
                                                            : Properties.Resources.SensorNotAvailableStatusText;
        }

        public void StopRecording()
        {
            if (this.isRecording)
            {
                this.socket.Send("StopRecording()", "stereorecorder");

                try
                {
                    int err = timeKillEvent(mTimerId);
                    timeEndPeriod(1);
                    mTimerId = 0;

                    int errskel = timeKillEvent(mTimerIdskel);
                    mTimerIdskel = 0;
                }
                catch (Exception ex)
                {

                }
                this.isRecording = false;
                //btnRecord.IsEnabled = false;

                if (this.waveIn != null)
                {
                    this.waveIn.StopRecording();
                }

                //this.FinalizeWaveFile();
                this.startTime = DateTime.MinValue;

                Thread.Sleep(500);
                //lock(this.imgBuffer)
                //{
                this.videoWriter.Dispose();
                //}
                this.skelWriter.Dispose();

                this.socket.Send("recording_completed(" + this.concept + "," + this.filenameBase + ")", "maingame");
            }
        }

        public void SetParticipantData(string participantID, string isYoungParticipant)
        {
            this.participantID = participantID;
            this.isYoungParticipant = false;

            if (participantID == "")
                participantID = "0";

            if (isYoungParticipant.ToLower() == "true")
                this.isYoungParticipant = true;            
        }

        public void exit()
        {
            System.Windows.Application.Current.Shutdown();
        }

        public void StartRecording(string concept, string isPractice = "false", string attemptNumber = "1")
        {
            // Message received from the main game --> start saving data (CSV and skeleton recording)

            this.hourglassSent = false;
            this.lastMeasured = DateTime.Now;
            this.totalRestTime = 0;
            this.totalActivityTime = 0;
            this.concept = concept;

            string exe_dir = System.Reflection.Assembly.GetEntryAssembly().Location;
            exe_dir = exe_dir.Substring(0, exe_dir.IndexOf(System.IO.Path.GetFileName(exe_dir)));

            this.filenameBase = DateTime.Now.ToString("yyyyMMddHHmmssffff") + "_" + this.participantID + "_" + attemptNumber;
            if (this.isYoungParticipant)
                this.filenameBase += "_under16";

            string dirname = "..\\..\\..\\..\\data\\recordings\\";
            if (isPractice.ToLower() == "true")
            {
                dirname = "..\\..\\..\\..\\data\\practice\\";
            }
            this.csvOut = exe_dir + dirname + concept + "\\" + this.filenameBase + ".csv";

            string outstr = "time," +
                "headposX,headposY,headposZ,neckposX,neckposY,neckposZ,rshoulderposX,rshoulderposY,rshoulderposZ,relbowposX,relbowposY,relbowposZ,rwristposX,rwristposY,rwristposZ," +
                "lshoulderposX,lshoulderposY,lshoulderposZ,lelbowposX,lelbowposY,lelbowposZ,lwristposX,lwristposY,lwristposZ,rhipposX,rhipposY,rhipposZ,rkneeposX,rkneeposY,rkneeposZ,rankleposX,rankleposY,rankleposZ," +
                "lhipposX,lhipposY,lhipposZ,lkneeposX,lkneeposY,lkneeposZ,lankleposX,lankleposY,lankleposZ,rfootposX,rfootposY,rfootposZ,lfootposX,lfootposY,lfootposZ,rhandposX,rhandposY,rhandposZ,lhandposX,lhandposY,lhandposZ," +
                "rhandtipposX,rhandtipposY,rhandtipposZ,lhandtipposX,lhandtipposY,lhandttipposZ,spinebaseposX,spinebaseposY,spinebaseposZ,spinemidposX,spinemidposY,spinemidposZ,spineshoulderposX,spineshoulderposY,spineshoulderposZ," +
                "rhandState,lhandState,rhandconfidence,lhandconfidence," +
                "rthumbposX,rthumbposY,rthumbposZ,lthumbposX,lthumbposY,lthumbposZ," +

                "neckoriX,neckoriY,neckoriZ,neckoriW,rshoulderoriX,rshoulderoriY,rshoulderoriZ,rshoulderoriW,relboworiX,relboxoriY,relboxoriZ,relboworiW,rwristoriX,rwristoriY,rwristoriZ,rwristoriW," +
                "lshoulderoriX,lshoulderoriY,lshoulderoriZ,lshoulderoriW,lelboworiX,lelboworiY,lelboworiZ,lelboworiW,lwristoriX,lwristoriY,lwristoriZ,lwristoriW,rhiporiX,rhiporiY,rhiporiZ,rhiporiW,rkneeoriX,rkneeoriY,rkneeoriZ,rkneeoriW,rankleoriX,rankleoriY,rankleoriZ,rankleoriW," +
                "lhiporiX,lhiporiY,lhiporiZ,lhiporiW,lkneeoriX,lkneeoriY,lkneeoriZ,lkneeoriW,lankleoriX,lankleoriY,lankleoriZ,lankleoriW,rhandoriX,rhandoriY,rhandoriZ,rhandoriW,lhandoriX,lhandoriY,lhandoriZ,lhandoriW," +
                "spinebaseoriX,spinebaseoriY,spinebaseoriZ,spinebaseoriW,spinemidoriX,spinemidoriY,spinemidoriZ,spinemidoriW,spineshoulderoriX,spineshoulderoriY,spineshoulderoriZ,spineshoulderoriW," +
                "facepitch,faceyaw,faceroll" +
                "\n";

            File.AppendAllText(this.csvOut, outstr);

            // Create video output
            this.videoWriter = new VideoWriter(exe_dir + dirname + concept + "\\" + this.filenameBase + ".avi", CvInvoke.CV_FOURCC('D', 'I', 'V', 'X'), 25, 960, 540, true);
            this.skelWriter = new VideoWriter(exe_dir + dirname + concept + "\\" + this.filenameBase + "_skel.avi", CvInvoke.CV_FOURCC('D', 'I', 'V', 'X'), 10, 640, 530, true);

            timeBeginPeriod(1);
            mHandler = new TimerEventHandler(SaveFrame);
            mTimerId = timeSetEvent(40, 0, mHandler, IntPtr.Zero, EVENT_TYPE);
            mTestStart = DateTime.Now;
            mTestTick = 0;

            mHandlerskel = new TimerEventHandler(SaveSkeleton);
            mTimerIdskel = timeSetEvent(100, 0, mHandlerskel, IntPtr.Zero, EVENT_TYPE);
            mTestStartskel = DateTime.Now;
            mTestTick = 0;

            // Start recording audio
            /*MMDeviceEnumerator deviceEnum = new MMDeviceEnumerator();
            MMDeviceCollection devices = deviceEnum.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);

            foreach (MMDevice d in devices)
            {
                if (d.DeviceFriendlyName == "Xbox NUI Sensor" && d.State == DeviceState.Active)
                {
                    if (this.waveIn != null)
                    {
                        this.waveIn.Dispose();
                        this.waveIn = null;
                    }
                    this.FinalizeWaveFile();

                    if (this.waveIn == null)
                    {
                        this.waveIn = new WasapiCapture(d);
                        this.waveIn.DataAvailable += OnWaveDataAvailable;
                    }
                    d.AudioEndpointVolume.Mute = false;
                    this.writer = new WaveFileWriter("output\\" + this.filenameBase + ".wav", this.waveIn.WaveFormat);
                    this.waveIn.StartRecording();

                    break;
                }
            }*/


            this.isRecording = true;
        }
    }
}
