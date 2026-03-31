namespace WinFormsApp1
{
    partial class FormRegister
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
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
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            FrmNickNameTxt = new Label();
            FrmPwdTxt = new Label();
            FrmPhoneTxt = new Label();
            FrmEmailTxt = new Label();
            FrmCodeTxt = new Label();
            TxtNickName = new TextBox();
            TxtCode = new TextBox();
            TxtEmail = new TextBox();
            TxtPhone = new TextBox();
            TxtPassWord = new TextBox();
            btnSendCode = new Button();
            btnRegister = new Button();
            btnClosed = new Button();
            SuspendLayout();
            // 
            // FrmNickNameTxt
            // 
            FrmNickNameTxt.AutoSize = true;
            FrmNickNameTxt.ImageAlign = ContentAlignment.MiddleRight;
            FrmNickNameTxt.Location = new Point(233, 109);
            FrmNickNameTxt.Name = "FrmNickNameTxt";
            FrmNickNameTxt.Size = new Size(46, 24);
            FrmNickNameTxt.TabIndex = 0;
            FrmNickNameTxt.Text = "匿名";
            // 
            // FrmPwdTxt
            // 
            FrmPwdTxt.AutoSize = true;
            FrmPwdTxt.ImageAlign = ContentAlignment.MiddleRight;
            FrmPwdTxt.Location = new Point(233, 189);
            FrmPwdTxt.Name = "FrmPwdTxt";
            FrmPwdTxt.Size = new Size(46, 24);
            FrmPwdTxt.TabIndex = 1;
            FrmPwdTxt.Text = "密码";
            // 
            // FrmPhoneTxt
            // 
            FrmPhoneTxt.AutoSize = true;
            FrmPhoneTxt.ImageAlign = ContentAlignment.MiddleRight;
            FrmPhoneTxt.Location = new Point(215, 274);
            FrmPhoneTxt.Name = "FrmPhoneTxt";
            FrmPhoneTxt.Size = new Size(64, 24);
            FrmPhoneTxt.TabIndex = 2;
            FrmPhoneTxt.Text = "手机号";
            // 
            // FrmEmailTxt
            // 
            FrmEmailTxt.AutoSize = true;
            FrmEmailTxt.ImageAlign = ContentAlignment.MiddleRight;
            FrmEmailTxt.Location = new Point(233, 361);
            FrmEmailTxt.Name = "FrmEmailTxt";
            FrmEmailTxt.Size = new Size(46, 24);
            FrmEmailTxt.TabIndex = 3;
            FrmEmailTxt.Text = "邮箱";
            // 
            // FrmCodeTxt
            // 
            FrmCodeTxt.AutoSize = true;
            FrmCodeTxt.ImageAlign = ContentAlignment.MiddleRight;
            FrmCodeTxt.Location = new Point(215, 436);
            FrmCodeTxt.Name = "FrmCodeTxt";
            FrmCodeTxt.Size = new Size(64, 24);
            FrmCodeTxt.TabIndex = 4;
            FrmCodeTxt.Text = "验证码";
            // 
            // TxtNickName
            // 
            TxtNickName.Location = new Point(306, 108);
            TxtNickName.Name = "TxtNickName";
            TxtNickName.Size = new Size(264, 30);
            TxtNickName.TabIndex = 5;
            TxtNickName.TextChanged += TxtNickName_TextChanged;
            // 
            // TxtCode
            // 
            TxtCode.Location = new Point(306, 432);
            TxtCode.Name = "TxtCode";
            TxtCode.Size = new Size(264, 30);
            TxtCode.TabIndex = 6;
            TxtCode.TextChanged += TxtCode_TextChanged;
            // 
            // TxtEmail
            // 
            TxtEmail.Location = new Point(306, 356);
            TxtEmail.Name = "TxtEmail";
            TxtEmail.Size = new Size(264, 30);
            TxtEmail.TabIndex = 7;
            TxtEmail.TextChanged += TxtEmail_TextChanged;
            // 
            // TxtPhone
            // 
            TxtPhone.Location = new Point(306, 269);
            TxtPhone.Name = "TxtPhone";
            TxtPhone.Size = new Size(264, 30);
            TxtPhone.TabIndex = 8;
            TxtPhone.TextChanged += TxtPhone_TextChanged;
            // 
            // TxtPassWord
            // 
            TxtPassWord.Location = new Point(306, 185);
            TxtPassWord.Name = "TxtPassWord";
            TxtPassWord.Size = new Size(264, 30);
            TxtPassWord.TabIndex = 9;
            TxtPassWord.TextChanged += TxtPassWord_TextChanged;
            // 
            // btnSendCode
            // 
            btnSendCode.Location = new Point(612, 425);
            btnSendCode.Name = "btnSendCode";
            btnSendCode.Size = new Size(133, 47);
            btnSendCode.TabIndex = 10;
            btnSendCode.Text = "发送";
            btnSendCode.UseVisualStyleBackColor = true;
            btnSendCode.Click += btnSendCode_Click;
            // 
            // btnRegister
            // 
            btnRegister.Location = new Point(215, 531);
            btnRegister.Name = "btnRegister";
            btnRegister.Size = new Size(133, 47);
            btnRegister.TabIndex = 11;
            btnRegister.Text = "注册";
            btnRegister.UseVisualStyleBackColor = true;
            btnRegister.Click += btnRegister_Click;
            // 
            // btnClosed
            // 
            btnClosed.Location = new Point(490, 531);
            btnClosed.Name = "btnClosed";
            btnClosed.Size = new Size(133, 47);
            btnClosed.TabIndex = 12;
            btnClosed.Text = "退出";
            btnClosed.UseVisualStyleBackColor = true;
            btnClosed.Click += btnClosed_Click;
            // 
            // FormRegister
            // 
            AutoScaleDimensions = new SizeF(11F, 24F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(875, 680);
            Controls.Add(btnClosed);
            Controls.Add(btnRegister);
            Controls.Add(btnSendCode);
            Controls.Add(TxtPassWord);
            Controls.Add(TxtPhone);
            Controls.Add(TxtEmail);
            Controls.Add(TxtCode);
            Controls.Add(TxtNickName);
            Controls.Add(FrmCodeTxt);
            Controls.Add(FrmEmailTxt);
            Controls.Add(FrmPhoneTxt);
            Controls.Add(FrmPwdTxt);
            Controls.Add(FrmNickNameTxt);
            Name = "FormRegister";
            StartPosition = FormStartPosition.CenterParent;
            Text = "FormRegister";
            Load += FormRegister_Load;
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Label FrmNickNameTxt;
        private Label FrmPwdTxt;
        private Label FrmPhoneTxt;
        private Label FrmEmailTxt;
        private Label FrmCodeTxt;
        private TextBox TxtNickName;
        private TextBox TxtCode;
        private TextBox TxtEmail;
        private TextBox TxtPhone;
        private TextBox TxtPassWord;
        private Button btnSendCode;
        private Button btnRegister;
        private Button btnClosed;
    }
}