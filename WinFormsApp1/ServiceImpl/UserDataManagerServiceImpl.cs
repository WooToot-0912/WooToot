using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;
using WinFormsApp1.Service;

namespace WinFormsApp1.ServiceImpl
{
    public class UserDataManagerServiceImpl: IUserDataManagerService
    {
        public IUserDataService UserDataService { get; set; }

        public UserDataManagerServiceImpl()
        {
            UserDataService = new UserDataServiceImpl();
        }

        /// <summary>
        /// 获取所用户信息
        /// </summary>
        /// <returns></returns>
        public List<User> GetUsers()
        {
            return UserDataService.GetUserList();

        }

        /// <summary>
        /// 根据id删除数据
        /// </summary>
        /// <param name="id"></param>
        public void DeleteById(string id)
        {
            UserDataService.DeleteUserByid(id);
        }
    }
}
