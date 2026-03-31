using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using WinFormsApp1.Models;

namespace WinFormsApp1.Utils
{
    /// <summary>
    /// 用户检查的工具类
    /// </summary>
    public class UserCheckUtil
    {
        private const int USER_COUNT=5;

        /// <summary>
        /// 检查用户是否输入
        /// </summary>
        /// <param name="str"></param>
        /// <returns></returns>
        public  static bool CheckUSerInput(string str)
        {
            return CheckUSerInput(str, USER_COUNT);
        }


        /// <summary>
        /// 检查用户是否输入
        /// </summary>
        /// <param name="str"></param>
        /// <returns></returns>
        public static bool CheckUSerInput(string str, int length)
        {
            if (string.IsNullOrEmpty(str) || str.Length < USER_COUNT)
            {
                return true;

            }
            return false;
        }

        /// <summary>
        /// 判断当前是否是一个邮箱
        /// </summary>
        /// <param name="userEmail">邮箱</param>
        /// <returns>是否是邮箱</returns>
        public static bool IsEmail(string userEmail)
        {
            //172893789 @ 32432.com
            //使用正则表达式检查邮箱格式
            string pattern = @"^[^@\s]+@[^@\s]+\.[^@\s]+$";
            return Regex.IsMatch(userEmail, pattern);
        }

        /// <summary>
        /// 判断当前是否是一个手机号
        /// </summary>
        /// <param name="userPhone"></param>
        /// <returns></returns>
        public static bool IsPhone(string userPhone)
        {
            //1 3-9 9
            //使用正则表达式检查邮箱格式
            //1 3-9 9
            string pattern = @"^1[3-9]\d{9}$";
            return Regex.IsMatch(userPhone, pattern);
        }

        /// <summary>
        /// 检查邮箱是否重复
        /// </summary>
        /// <param name="email"></param>
        /// <returns></returns>
        public static bool CheckEmailRepeact(string email)
        {
            UserDb userDb = UserDb.GetUserDb();
            foreach (var user in userDb.Users)
            {
                if (user.Email == email)
                {
                    return false;
                }
            }

            return true;
        }
    }
}
