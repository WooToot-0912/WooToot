using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;

namespace WinFormsApp1.Service
{
    /// <summary>
    /// 用户服务
    /// </summary>
    public interface IUserService
    {

        /// <summary>
        /// 登录
        /// </summary>
        /// <param name="userName"></param>
        /// <param name="PassWord"></param>
        /// <returns></returns>
        bool Login(User user);

        /// <summary>
        /// 注册
        /// </summary>
        /// <param name="user"></param>
        /// <returns></returns>
        bool Register(User user);

        /// <summary>
        /// 记录用户信息
        /// </summary>
        /// <param name="user"></param>
        /// <returns></returns>
        void RememberMe(User user);

        /// <summary>
        /// 获取记住的用户信息
        /// </summary>
        /// <returns></returns>
        User GetRememberUser();
    }

}
