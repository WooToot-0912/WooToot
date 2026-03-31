using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;

namespace WinFormsApp1.Utils
{
    /// <summary>
    /// 用户账号工具类
    /// </summary>
    public class UserCountUtil
    {
        const int Length = 6;
        /// <summary>
        /// 生成随机账号
        /// </summary>
        /// <param name="length"></param>
        /// <returns></returns>
        public static string CreateCount(int length)
        {
        newCount:
            //TODO: 生成用户账号
            Random r = new Random();
            string userCount = "";
            for (int i = 0; i < length; i++)
            {
                userCount += r.Next(9);
            }
            if (checkuserCountRepeact(userCount))
            {
                return userCount;
            }
            else
            {
                goto newCount;
            }
        }

        /// <summary>
        /// 检查账号是否重复
        /// </summary>
        /// <exception cref="NotImplementedException"></exception>
        private static bool checkuserCountRepeact(string userCount)
        {
            UserDb userDb = UserDb.GetUserDb();
            foreach(var user in userDb.Users)
            {
                if(user.UserName == userCount)
                {
                    return false;
                }
            }

            return true;
        }


        /// <summary>
        /// 生成随机账号
        /// </summary>
        /// <param name="length"></param>
        /// <returns></returns>
        public static string CreateCount()
        {
            return CreateCount(Length);
        }
    }
}
