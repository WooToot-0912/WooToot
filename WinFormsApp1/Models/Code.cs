using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WinFormsApp1.Models
{
    public class Code
    {

        /// <summary>
        /// 带空格的验证码
        /// </summary>
        public string OldCode;

        /// <summary>
        /// 不带空格的验证码
        /// </summary>
        public string NewCode;

        /// <summary>
        /// 过期时间
        /// </summary>
        public DateTime Expiration;

        /// <summary>
        /// 用户输入的验证码
        /// </summary>
        //public string UserInputCode;
    }
}
