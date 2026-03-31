using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using WinFormsApp1.Models;
using WinFormsApp1.Service;
using WinFormsApp1.ServiceImpl;
using WinFormsApp1.Utils;

namespace WinFormsApp1
{
    public partial class FormRegister : Form
    {

        /// <summary>
        /// 注入用户服务
        /// </summary>
        private IUserService userService { get; set; }

        private Code code { get; set; }

        /// <summary>
        /// 验证码服务
        /// </summary>
        private ICodeService Codeservice { get; set; }

        private void FormRegister_Load(object sender, EventArgs e)
        {
            userService = new UserServiceImpl();
            Codeservice = new CodeServiceImpl();
            this.btnRegister.Enabled = false;//一开始注册按钮不允许使用
        }

        public FormRegister()
        {
            InitializeComponent();
        }

        private void btnClosed_Click(object sender, EventArgs e)
        {
            this.Close();
        }

        /// <summary>
        /// 注册
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void btnRegister_Click(object sender, EventArgs e)
        {
            User user = new User();
            //获取命名
            user.NickName = TxtNickName.Text.Trim();
            //user.UserName = TxtUserName.Text.Trim();
            //user.Password = TxtPassword.Text.Trim();
            user.Email = TxtEmail.Text.Trim();
            user.Phone = TxtPhone.Text.Trim();
            user.PassWord = TxtPassWord.Text.Trim();

            if (UserCheckUtil.CheckUSerInput(TxtCode.Text.Trim(), 1))
            {
                MessageBox.Show("验证码输入错误");
                //MyLog<FormRegister>.LogDebug("验证码输入错误");
                return;
            }

            if (!Codeservice.CheckCodeExpiration(code))
            {
                MessageBox.Show("验证码已过期");
                //MyLog<FormRegister>.LogDebug("验证码已过期");
                return;
            }

            if (!Codeservice.CheckCode(code, TxtCode.Text.Trim()))
            {
                MessageBox.Show("验证码错误，请重新发送");
                //MyLog<FormRegister>.LogDebug("验证码错误，请重新发送");
                return;

            }


            if (userService.Register(user))
            {
                MessageBox.Show("注册成功！");
                this.Close();
            }
            else
            {
                MessageBox.Show("注册失败！手机号已经存在");
                TxtPhone.Clear();

            }


            userService.Register(user);
        }


        /// <summary>
        /// 键盘是否输入
        /// </summary>
        private void WahtchText()
        {
            string nickName = TxtNickName.Text.Trim();
            string email = TxtEmail.Text.Trim();
            string phone = TxtPhone.Text.Trim();
            string password = TxtPassWord.Text.Trim();
            string EmailCode = TxtCode.Text.Trim();

            if (UserCheckUtil.IsEmail(email) && UserCheckUtil.IsPhone(phone)
                && !(UserCheckUtil.CheckUSerInput(EmailCode, 4) && UserCheckUtil.CheckUSerInput(nickName, 1) && UserCheckUtil.CheckUSerInput(phone)
                && UserCheckUtil.CheckUSerInput(password) && UserCheckUtil.CheckUSerInput(email)))
            {
                this.btnRegister.Enabled = true;
                return;
            }
            else
            {
                this.btnRegister.Enabled = false;
            }
        }

        private void TxtNickName_TextChanged(object sender, EventArgs e)
        {
            WahtchText();
        }

        private void TxtPassWord_TextChanged(object sender, EventArgs e)
        {
            WahtchText();
        }

        private void TxtPhone_TextChanged(object sender, EventArgs e)
        {
            WahtchText();
        }

        private void TxtEmail_TextChanged(object sender, EventArgs e)
        {
            WahtchText();
        }

        /// <summary>
        /// 验证码输入框文本改变
        /// </summary>
        private void TxtCode_TextChanged(object sender, EventArgs e)
        {
            WahtchText();
        }

        /// <summary>
        /// 发送验证码按钮点击
        /// </summary>
        private void btnSendCode_Click(object sender, EventArgs e)
        {
            try
            {
                // 调试信息:检查邮箱是否为空
                if (UserCheckUtil.CheckUSerInput(TxtEmail.Text))
                {
                    MessageBox.Show("请输入邮箱之后尝试");
                    return;
                }

                // 调试信息:检查邮箱格式
                if (!UserCheckUtil.IsEmail(TxtEmail.Text))
                {
                    MessageBox.Show("请输入正确的邮箱");
                    return;
                }

                // 调试信息:检查邮箱是否已注册
                if (UserCheckUtil.CheckEmailRepeact(TxtEmail.Text))
                {
                    MessageBox.Show("邮箱已经注册过");
                    return;
                }

                // 发送验证码
                string userEmail = TxtEmail.Text.Trim();
                code = Codeservice.CreateCode();
                
                // 添加调试信息
                MessageBox.Show($"正在发送验证码到: {userEmail}");
                
                Codeservice.SendVerificationCode(userEmail, code.NewCode);

                // 显示成功消息
                MessageBox.Show("验证码已发送,请查收邮箱!");

                // 禁用按钮并开始倒计时
                btnSendCode.Enabled = false;
                int time = 60;

                var timer = new System.Windows.Forms.Timer();
                timer.Interval = 1000; // 1秒间隔
                timer.Tick += (s, args) =>
                {
                    time--;
                    btnSendCode.Text = $"{time}秒后重试";

                    if (time <= 0)
                    {
                        timer.Stop();
                        timer.Dispose();
                        btnSendCode.Text = "发送验证码";
                        btnSendCode.Enabled = true;
                    }
                };
                timer.Start();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"发送验证码时出错: {ex.Message}\n\n详细信息:\n{ex.StackTrace}");
                btnSendCode.Enabled = true;
            }
        }

    }
}
