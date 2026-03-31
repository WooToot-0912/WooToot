namespace WinFormsApp1
{
    partial class Form1
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            label1 = new Label();
            btnLogin = new Button();
            label2 = new Label();
            button2 = new Button();
            button3 = new Button();
            txtUserName = new TextBox();
            txtPwd = new TextBox();
            ckLogin = new CheckBox();
            SuspendLayout();
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Location = new Point(201, 96);
            label1.Name = "label1";
            label1.Size = new Size(76, 24);
            label1.TabIndex = 0;
            label1.Text = "QQ账号";
            // 
            // btnLogin
            // 
            btnLogin.Enabled = false;
            btnLogin.Location = new Point(230, 259);
            btnLogin.Name = "btnLogin";
            btnLogin.Size = new Size(335, 57);
            btnLogin.TabIndex = 1;
            btnLogin.Text = "登录";
            btnLogin.UseVisualStyleBackColor = true;
            btnLogin.Click += button1_Click;
            // 
            // label2
            // 
            label2.AutoSize = true;
            label2.Location = new Point(201, 193);
            label2.Name = "label2";
            label2.Size = new Size(76, 24);
            label2.TabIndex = 2;
            label2.Text = "QQ密码";
            // 
            // button2
            // 
            button2.Location = new Point(151, 349);
            button2.Name = "button2";
            button2.Size = new Size(126, 57);
            button2.TabIndex = 3;
            button2.Text = "注册";
            button2.UseVisualStyleBackColor = true;
            button2.Click += btnRegister_Click;
            // 
            // button3
            // 
            button3.Location = new Point(516, 349);
            button3.Name = "button3";
            button3.Size = new Size(129, 57);
            button3.TabIndex = 4;
            button3.Text = "退出";
            button3.UseVisualStyleBackColor = true;
            button3.Click += button3_Click;
            // 
            // txtUserName
            // 
            txtUserName.BackColor = SystemColors.Window;
            txtUserName.Location = new Point(297, 83);
            txtUserName.Multiline = true;
            txtUserName.Name = "txtUserName";
            txtUserName.Size = new Size(247, 45);
            txtUserName.TabIndex = 5;
            txtUserName.TextChanged += txtUserName_TextChanged;
            // 
            // txtPwd
            // 
            txtPwd.Location = new Point(297, 183);
            txtPwd.Multiline = true;
            txtPwd.Name = "txtPwd";
            txtPwd.Size = new Size(247, 44);
            txtPwd.TabIndex = 6;
            txtPwd.TextChanged += txtPwd_TextChanged;
            // 
            // ckLogin
            // 
            ckLogin.AutoSize = true;
            ckLogin.Location = new Point(589, 274);
            ckLogin.Name = "ckLogin";
            ckLogin.Size = new Size(108, 28);
            ckLogin.TabIndex = 7;
            ckLogin.Text = "自动登录";
            ckLogin.UseVisualStyleBackColor = true;
            // 
            // Form1
            // 
            AutoScaleDimensions = new SizeF(11F, 24F);
            AutoScaleMode = AutoScaleMode.Font;
            BackgroundImage = Resource.Login;
            BackgroundImageLayout = ImageLayout.Stretch;
            ClientSize = new Size(780, 469);
            Controls.Add(ckLogin);
            Controls.Add(txtPwd);
            Controls.Add(txtUserName);
            Controls.Add(button3);
            Controls.Add(button2);
            Controls.Add(label2);
            Controls.Add(btnLogin);
            Controls.Add(label1);
            Name = "Form1";
            StartPosition = FormStartPosition.CenterParent;
            Text = "QQ管理系统";
            Load += Form1_Load;
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Label label1;
        private Button btnLogin;
        private Label label2;
        private Button button2;
        private Button button3;
        private TextBox txtUserName;
        private TextBox txtPwd;
        private CheckBox ckLogin;
    }
}
