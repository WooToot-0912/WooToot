using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WinFormsApp1.Models
{
    public class GlobalUser
    {
        /// <summary>
        /// 用户Id
        /// </summary>
        public static string Id { get; set; }

        /// <summary>
        /// 没有加密的密码
        /// </summary>
        public static string PassWord { get; set; }

    }
}
