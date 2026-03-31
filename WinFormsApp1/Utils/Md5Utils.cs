using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;

namespace WinFormsApp1.Utils
{
    public class Md5Utils
    {
        /// <summary>
        /// 加密MD5
        /// </summary>
        /// <param name="pwd">明文</param>
        /// <returns>密文</returns>
        public static string GetMd5(string pwd)
        {
            pwd += Salt.encrySalt;
            //1.创建md5对象
            MD5 md5 = MD5.Create();
            //2.我们需要把我们的字符串通过md5对象进行加密  字节  字符串转换成字节数组
            byte[] buffer = Encoding.UTF8.GetBytes(pwd);
            //3.对字节数组进行加密
            byte[] newBuffer = md5.ComputeHash(buffer);//通过hash算法进行加密

            //4.需要把加密后的字节数组转换成16进制的字符串 *2
            StringBuilder sb = new StringBuilder();

            for (int i=0; i<newBuffer.Length; i++)
            {
                sb.Append(newBuffer[i].ToString("x2"));

            }

            return sb.ToString();


        }
    }
}
