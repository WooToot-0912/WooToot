using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Mail;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;

namespace WinFormsApp1.Service
{

    /// <summary>
    /// 验证码服务接口
    /// </summary>
    public interface ICodeService
    {


        /// <summary>
        /// 发送验证码
        /// </summary>
        /// <param name="toEmail"></param>
        /// <param name="verificationCode"></param>
        public void SendVerificationCode(string toEmail, string verificationCode);
        

        /// <summary>
        /// 生成验证码
        /// </summary>
        /// <returns></returns>
        public Code CreateCode();
        //void SendVerificationCode(Code code);

        /// <summary>
        /// 校验验证码
        /// </summary>
        /// <param name="userCode">用户输入的验证码</param>
        /// <param name="systemCode">系统生成的验证码</param>
        /// <returns>验证码是否正确</returns>
        public bool CheckCode(Code systemCode, string UserCode);

        /// <summary>
        /// 检查验证码是否过期
        /// </summary>
        /// <param name="code">验证码对象</param>
        /// <returns>是否过期</returns>
        public bool CheckCodeExpiration(Code code);
    }
}
