using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Mail;
using System.Security;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;
using WinFormsApp1.Service;
using WinFormsApp1.Utils;

namespace WinFormsApp1.ServiceImpl
{
    public class CodeServiceImpl : ICodeService
    {
        //QQ邮箱SMTP服务器配置
        private const string SmtpService = "smtp.qq.com";
        private const int SmtpPort = 587; // 使用587端口(STARTTLS)
        private const string FromEmail = "1950383511@qq.com";//你的邮箱账号
        private const string FromPassword = "qrfbhhtshzyjcfee";//你的邮箱授权码

        //鉴权  //改造
        /// <summary>
        /// 验证码来源
        /// </summary>
        const string CODE_SOURCE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

        /// <summary>
        /// 验证码过期时间
        /// </summary>
        const int CODE_EXPIRATION_TIME = 60;


        /// <summary>
        /// 发送验证码
        /// </summary>
        /// <param name="toEmail"></param>
        /// <param name="verificationCode"></param>
        public void SendVerificationCode(string toEmail, string verificationCode)
        {
            try
            {
                //创建邮件消息
                var mailMessage = new MailMessage
                {
                    From = new MailAddress(FromEmail),
                    Subject = "qq注册验证码",
                    Body = $"您的验证码是：{verificationCode},有效期为60s。请勿泄露",
                    IsBodyHtml = false //设置为true可以发送HTML格式邮件
                };
                //发送给谁
                mailMessage.To.Add(toEmail);

                //创建SMTP客户端
                var smtpClient = new SmtpClient(SmtpService)
                {
                    Port = SmtpPort,
                    Credentials = new System.Net.NetworkCredential(FromEmail, FromPassword),
                    EnableSsl = true //使用SSL加密
                };

                //发送邮件
                smtpClient.Send(mailMessage);

                // MyLog<CodeServiceImpl>.LogDebug("验证码邮件发送成功！发送的验证码为：" + verificationCode);

                Console.WriteLine("验证码已发送至邮箱：" + toEmail);

            }
            catch (Exception ex)
            {
                Console.WriteLine("验证码发送失败：" + ex.Message);
                throw; //根据你的需求处理异常
            }
        }

        public Code CreateCode()
        {
            //TODO 验证码过期时间没有做
            //code ===>  过期时间  带空格的验证码  不带空格的验证码
            //string code = null
            Code code = new Code();
            Random r = new Random();
            for (int i=0; i<4; i++)
            {
                int number = r.Next(0, CODE_SOURCE.Length);
                code.OldCode += CODE_SOURCE[number] + " ";
                code.NewCode += CODE_SOURCE[number];
            }

            //过期时间
            //23----->  24
            //时间 25
            //23-----> 20
            code.Expiration = DateTime.Now.AddSeconds(CODE_EXPIRATION_TIME);

            //Console.WriteLine(code.OldCode);
            //Console.WriteLine(code.NewCode);

            return code;

        }

        /// <summary>
        /// 校验验证码
        /// </summary>
        /// <param name="usercode">用户输入的验证码</param>
        /// <param name="systemCode">系统生成的验证码</param>
        /// <returns></returns>
        public bool CheckCode(Code systemCode, string UserCode)
        {

            //AcdF
            //acdf
            //用户 不管输入大写还是小写都可以校验成功
            //ToUpper==把字符串转大写
            if(UserCode.ToUpper() == systemCode.NewCode.ToUpper())
            {
                return true;
            }
            return false;
        }

        /// <summary>
        /// 检查验证码是否过期
        /// </summary>
        /// <param name="code"></param>
        /// <returns></returns>
        public bool CheckCodeExpiration(Code code)
        {
            if(code.Expiration < DateTime.Now)
            {
                return true;
            }
            return false;
        }
    }
}
