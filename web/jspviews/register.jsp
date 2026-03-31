<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>注册 - 旅游项目管理系统</title>
  <link rel="stylesheet" href="../css/register.css">
</head>
<body>
<div class="register-container">
  <h2>管理员注册</h2>

  <!-- 显示错误信息 -->
  <% if(request.getAttribute("error") != null) { %>
  <div class="error-message">
    <%= request.getAttribute("error") %>
  </div>
  <% } %>

  <form action="register.do" method="post">
    <div class="form-group">
      <label for="username">用户账号（请输入数字ID）：</label>
      <input type="text" id="username" name="username" pattern="[0-9]+"
             title="请输入数字ID" required>
    </div>
    <div class="form-group">
      <label for="password">密码：</label>
      <input type="password" id="password" name="password" required>
    </div>
    <div class="form-group">
      <label for="confirmPassword">确认密码：</label>
      <input type="password" id="confirmPassword" name="confirmPassword" required>
    </div>
    <div class="form-buttons">
      <button type="submit">注册</button>
      <a href="login.jsp">返回登录</a>
    </div>
  </form>
</div>
</body>
</html>