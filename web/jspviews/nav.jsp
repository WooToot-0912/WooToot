<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>

<%
    // 添加调试信息
    System.out.println("Nav - Current user in session: " + session.getAttribute("loginuser"));
%>

<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>导航栏</title>
    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="../css/nav.css">
    <link rel="stylesheet" href="../fonts/fontawesome-free-6.4.0-web/css/all.min.css">
</head>
<body>
<nav class="sidebar">
    <div class="logo">
        <img src="../images/2-12.png" alt="Logo">
        <span class="company-name">旅游共享记账系统</span>
    </div>
    <ul class="nav-links">
        <li><a href="index.jsp" target="_parent"><i class="fas fa-home"></i>首页</a></li>
        <c:if test="${sessionScope.loginuser != null}">
            <li><a href="add-team.jsp" target="_parent"><i class="fas fa-users"></i>添加团队</a></li>
            <li><a href="edit-project.jsp" target="_parent"><i class="fas fa-edit"></i>编辑项目</a></li>
            <li><a href="view-bill.jsp" target="_parent"><i class="fas fa-file-invoice"></i>查看账单</a></li>
        </c:if>
    </ul>
    <div class="user-section">
        <c:choose>
            <c:when test="${sessionScope.loginuser != null}">
                <div class="user-info">
                    <i class="fas fa-user"></i>
                    <span>${sessionScope.loginuser.userid}</span>
                    <button onclick="logout()" class="logout-btn">
                        <i class="fas fa-sign-out-alt"></i> 退出登录
                    </button>
                </div>
            </c:when>
            <c:otherwise>
                <div class="login-status">
                    <i class="fas fa-exclamation-circle"></i>
                    <span class="login-tip">您还未登录，请</span>
                    <a href="login.jsp" target="_parent">登录</a>
                </div>
            </c:otherwise>
        </c:choose>
    </div>
</nav>

<!-- 添加登出处理的JavaScript -->
<script>
    function logout() {
        if(confirm('确定要退出登录吗？')) {
            window.parent.location.href = 'logout.do';
        }
    }
</script>
</body>
</html>