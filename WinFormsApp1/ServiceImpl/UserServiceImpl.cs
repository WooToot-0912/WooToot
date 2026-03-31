using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;
using WinFormsApp1.Service;
using WinFormsApp1.Utils;

namespace WinFormsApp1.ServiceImpl
{

    public class UserServiceImpl : IUserService
    {
        string path = "Users\\RememberMe.txt";
        /// <summary>
        /// 用户数据
        /// </summary>
        private UserDb userDb { get; set; }

        /// <summary>
        /// 用户本地数据服务
        /// </summary>
        public IUserDataService userDataService { get; set; }

        public UserServiceImpl()
        {
            // userDb = new UserDb();
            userDb = UserDb.GetUserDb();
            userDataService=new UserDataServiceImpl();
        }



        /// <summary>
        /// 登录
        /// </summary>
        /// <param name="userName"></param>
        /// <param name="PassWord"></param>
        /// <returns></returns>
        /// <exception cref="NotImplementedException"></exception>
        public bool Login(User user)
        {
            if (user == null)
            {
                return false;
            }
            //if(user.UserName == "admin" && user.PassWord == "123456")
            //{
            //    return true;
            //}

            GlobalUser.PassWord = user.PassWord;
            user.PassWord = Md5Utils.GetMd5(user.PassWord);

            foreach (var item in userDb.Users)
            {
                if(item.UserName == user.UserName && item.PassWord == user.PassWord)
                {
                    //item详细的信息

                    GlobalUser.Id = item.Id;
                    
                    return true;
                }
            }

            return false;
        }

        /// <summary>
        /// 注册
        /// </summary>
        /// <param name="user"></param>
        /// <returns></returns>
        /// <exception cref="NotImplementedException"></exception>
        public bool Register(User user)
        {

            //判断用户传入的内容不为空
            if(user == null || UserCheckUtil.CheckUSerInput(user.NickName, 1) || UserCheckUtil.CheckUSerInput(user.PassWord,3) || UserCheckUtil.CheckUSerInput(user.Phone,4))
            {
                return false;
            }

            foreach (var item in userDb.Users)
            {
                if(user.Phone == item.Phone)
                {
                    return false;
                }
            }

            user.PassWord = Md5Utils.GetMd5(user.PassWord);
            user.UserName = UserCountUtil.CreateCount();

            //存储到本地
            userDataService.SaveUser(user);

            //TODO  存储数据
            // userDb.Users.Add(user);

            //把获取到的本地信息存储到user里面
            userDb.Users = userDataService.GetUserList();

            MessageBox.Show("您的账号为：" + user.UserName + "，请牢记您的账号和密码！");

            return true;

        }

        /// <summary>
        /// 记录用户信息
        /// </summary>
        /// <param name="user"></param>
        /// <returns></returns>
        void RememberMe(User user)
        {
            if(user == null)
            {
                return;
            }

            string localUser = EncryUser(user);
            using (StreamWriter sw = new StreamWriter(path))
            {
                //覆盖当前的文件
                sw.WriteLine(localUser);
            }
        }

        /// <summary>
        /// 对用户信息进行加密
        /// </summary>
        /// <param name="user"></param>
        /// <returns></returns>
        /// <exception cref="NotImplementedException"></exception>
        private string EncryUser(User user)
        {

            StringBuilder sb = new StringBuilder();
            sb.Append($"{user.Id}  {user.UserName}  {GlobalUser.PassWord}");
            return sb.ToString();
        }

        /// <summary>
        /// 获取记住的用户信息
        /// </summary>
        /// <returns></returns>
        public User GetRememberUser()
        {
            User users = new User();
            //1.读取本地文件
            string localUser = null;
            using (StreamReader sw = new StreamReader(path))
            {
                while (!sw.EndOfStream)
                {
                    localUser = sw.ReadLine();

                    users = ParseUser(localUser);
                }
            }

            //2.解析用户信息
            //3.构造用户对象
            //4.存储本地用户模型

            return users;
        }

        /// <summary>
        /// 解析用户信息
        /// </summary>
        /// <param name="localUser"></param>
        private User ParseUser(string localUser)
        {
            User user = new User();
            string[] users = localUser.Split(" ", StringSplitOptions.RemoveEmptyEntries);
            try
            {
                //3.构造用户对象

                user.Id = users[0];
                user.UserName = users[1];
                user.PassWord = users[2];

            }
            catch
            {

            }


            return user;
        }

        void IUserService.RememberMe(User user)
        {
            RememberMe(user);
        }
    }
}
