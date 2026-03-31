using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;

namespace WinFormsApp1.Service
{
    /// <summary>
    /// 用户本地数据服务
    /// </summary>
    public interface IUserDataService
    {
        /// <summary>
        /// 保存用户接口
        /// </summary>
        /// <returns></returns>
        bool SaveUser(User user);

        /// <summary>
        /// 获取用户
        /// </summary>
        /// <returns></returns>
        List<User> GetUserList();

        /// <summary>
        /// g根据Id获取用户
        /// </summary>
        /// <param name="id"></param>
        /// <returns></returns>
        User GetUserById(string Id);

        /// <summary>
        /// 根据id更新用户
        /// </summary>
        /// <param name="id"></param>
        /// <param name="user"></param>
        /// <returns></returns>
        void UpdateUserById(string id, User user);

        /// <summary>
        /// 删除所有用户信息
        /// </summary>
        void DeleteUserList();

        /// <summary>
        /// 根据id删除用户
        /// </summary>
        /// <param name="id"></param>
        public void DeleteUserByid(string id);

        /// <summary>
        /// 根据id查找用户
        /// </summary>
        /// <param name="id"></param>
        public User GetUserByid(string id);
    }
}
