using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Service;
using WinFormsApp1.ServiceImpl;

namespace WinFormsApp1.Models
{

    /// <summary>
    /// 本地用户
    /// </summary>
    public class UserDb
    {
        private static UserDb userDb;

        //单例设计模式
        public List<User> Users { get; set; }

        public IUserDataService UserDataService { get; set; }

        //1.构造方法私有化
        private UserDb()
        {
            InitUser();
        }

        /// <summary>
        /// 初始化本地用户信息
        /// </summary>
        private void InitUser()
        {
            Users = new List<User>();
            UserDataService = new UserDataServiceImpl();
            //User userl = new User() { UserName = "admin", Email = "1950383511@qq.com", Phone = "17608840912", PassWord = "123456", NickName = "WOOTOOT" };
            //Users.Add(userl);
            Users = UserDataService.GetUserList();

        }

        public static UserDb GetUserDb()
        {
            if(userDb == null)
            {
                userDb = new UserDb();

            }

            return userDb;

        }

    }
}
