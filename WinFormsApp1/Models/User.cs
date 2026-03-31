using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace WinFormsApp1.Models
{
    /// <summary>
    /// 用户实体
    /// </summary>
    public class User
    {
        /// <summary>
        /// 用户id 保证用户的唯一性
        /// </summary>
        public string Id { get; set; }

        /// <summary>
        /// 账号
        /// </summary>
        public string UserName { get; set; }
        
        /// <summary>
        /// 密码
        /// </summary>
        public string PassWord { get; set; }
        
        /// <summary>
        /// 邮箱
        /// </summary>
        public string Email { get; set; }
        
        /// <summary>
        /// 手机号
        /// </summary>
        public string Phone { get; set; }
        
        /// <summary>
        /// 注册时间
        /// </summary>
        public DateTime CreateTime { get; set; }
        
        /// <summary>
        /// 昵称
        /// </summary>
        public string NickName { get; set; }
        
        /// <summary>
        /// 更新时间
        /// </summary>
        public DateTime UpdateTime { get; set; }

        /// <summary>
        /// 是否被删除 true 用户删除了   false 用户没有被删除
        /// </summary>
        public bool IsDatected { get; set; }


        public override string ToString()
        {
            return $"{NickName} \t {UserName}\t {PassWord} \t {Email} \t {Phone} \t{IsDatected}";
        }

        public string DisPlayInfo { get 
            {
                return $"{NickName} \t {UserName}\t {PassWord} \t {Email} \t {Phone} \t{IsDatected}";

            } 

        }

    }
}
