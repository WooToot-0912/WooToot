using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;

namespace WinFormsApp1.Service
{
    public interface IUserDataManagerService
    {
        /// <summary>
        /// 获取所用户信息
        /// </summary>
        /// <returns></returns>
        public List<User> GetUsers();


        /// <summary>
        /// 根据id删除数据
        /// </summary>
        /// <param name="id"></param>
        public void DeleteById(string id);
    }
}
