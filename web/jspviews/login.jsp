<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - 旅游项目管理系统</title>
    <link rel="stylesheet" href="../css/login.css">
</head>
<body>
<%
    // 检查是否已经登录
    if(session.getAttribute("loginuser") != null) {
        // 如果已登录，直接跳转到首页
        response.sendRedirect("index.jsp");
        return;
    }
%>

<div class="login-container">
    <div class="login-box">
        <h2>管理员登录</h2>

        <!-- 显示错误信息 -->
        <% if(request.getAttribute("error") != null) { %>
        <div class="error-message">
            <%= request.getAttribute("error") %>
        </div>
        <% } %>

        <form action="login.do" method="post">
            <div class="form-group">
                <label for="username">用户账号：</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">密码：</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="form-buttons">
                <button type="submit">登录</button>
                <a href="register.jsp">注册新账号</a>
            </div>
        </form>
    </div>
</div>
</body>
</html>