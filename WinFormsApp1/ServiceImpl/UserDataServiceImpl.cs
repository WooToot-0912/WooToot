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
    public class UserDataServiceImpl : IUserDataService
    {
        /// <summary>
        /// 所有用户信息的路径
        /// </summary>
        private const string path =@"Users\\users.txt";

        /// <summary>
        /// 获取所有用户
        /// </summary>
        /// <returns></returns>
        /// <exception cref="NotImplementedException"></exception>
        public List<User> GetUserList()
        {
            List<User> users = new List<User>();
            //1.读取本地文件
            string localUser = null;
            using (StreamReader sw = new StreamReader(path))
            {
                while (!sw.EndOfStream)
                {
                    localUser = sw.ReadLine();

                    users.Add(ParseUser(localUser));
                }
            }

            //2.解析用户信息
            
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
                user.NickName = users[1];
                user.UserName = users[2];
                user.PassWord = users[3];
                user.Email = users[4];
                user.Phone = users[5];
                user.IsDatected = bool.Parse(users[6]);
            }
            catch
            {

            }
            

            return user;
        }

        /// <summary>
        /// 保存用户接口
        /// </summary>
        /// <returns></returns>
        /// <exception cref="NotImplementedException"></exception>
        public bool SaveUser(User user)
        {
            if(user == null)
            {
                return false;
            }

            string localUser = EncryUser(user);
            using (StreamWriter sw = new StreamWriter(path,true))
            {
                //覆盖当前的文件
                sw.WriteLine(localUser);
            }
            return true;

        }

        /// <summary>
        /// 加密用户
        /// </summary>
        private string EncryUser(User user)
        {
            //1+2 //重复
            //GUID
            user.Id = Guid.NewGuid().ToString();
            StringBuilder sb = new StringBuilder();
            sb.Append($"{user.Id}  {user.NickName}  {user.UserName}  {user.PassWord}  {user.Email}  {user.Phone}  {user.IsDatected}\r\n");
            return sb.ToString();

        }

        /// <summary>
        /// g根据Id获取用户
        /// </summary>
        /// <param name="id"></param>
        /// <returns></returns>
        public User GetUserById(string id)
        {
            //1.获取所有用户
            List<User> users = GetUserList();
            User userBack = new User();
            foreach (User user in users)
            {
                if (user.Id == id)
                {
                    userBack.Id = user.Id;
                    userBack.NickName = user.NickName;
                    userBack.Email = user.Email;
                    userBack.Phone = user.Phone;
                    userBack.PassWord = GlobalUser.PassWord;
                    userBack.UserName = user.UserName;

                    break;
                }
            }
            return userBack;
        }

        /// <summary>
        /// 根据id更新用户
        /// </summary>
        /// <param name="id"></param>
        /// <param name="user"></param>
        /// <returns></returns>
        public void UpdateUserById(string id, User user)
        {
            //1.拿到所有的用户信息
            List<User> users = GetUserList();

            //2.删除数据
            DeleteUserList();

            //3.重新创建文件
            FileStream fs = File.Create(path);
            fs.Flush();
            fs.Dispose();
            fs.Close();

            //4.重新构建用户
            foreach (var item in users)
            {
                if(item.Id == id)
                {
     
                    item.NickName = user.NickName;
                    item.Email = user.Email;
                    item.Phone = user.Phone;
                    item.PassWord = Md5Utils.GetMd5(GlobalUser.PassWord);

                }
                //5.保存用户信息
                SaveUser(item);
            }
        }

        /// <summary>
        /// 删除所有用户信息
        /// </summary>
        public void DeleteUserList()
        {
            //1.删除本地文件
            File.Delete(path);
        }

        /// <summary>
        /// 根据id查找用户
        /// </summary>
        /// <param name="id"></param>
        public User GetUserByid(string id)
        {
            return null;
        }

        /// <summary>
        /// 根据id删除用户
        /// </summary>
        /// <param name="id"></param>
        public void DeleteUserByid(string id)
        {
            //1.拿到所有的用户信息
            List<User> users = GetUserList();

            List<User> user1 =new List<User>();
            //2.删除数据
            DeleteUserList();

            //3.重新创建文件
            FileStream fs = File.Create(path);
            fs.Flush();
            fs.Dispose();
            fs.Close();

            //4.重新构建用户
            foreach (var item in users)
            {
                if (item.Id != id)
                {
                    user1.Add(item);
                    continue;

                }
            }
            foreach (var item in user1)
            {
                SaveUser(item);
            }
        }
    }
}
