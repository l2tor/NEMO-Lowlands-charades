using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Microsoft.Samples.Kinect.BodyBasics
{
    class JointObject
    {
        public string input_type = "kinect";
        public List<List<float>> joints;

        public JointObject(List<List<float>> joints)
        {
            this.joints = joints;
        }
    }
}
