<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<!DOCTYPE html>
<html>
<head>
    <title>错误提示</title>
    <link rel="stylesheet" href="../css/style.css">
    <style>
        .error-container {
            max-width: 500px;
            margin: 100px auto;
            padding: 20px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .error-icon {
            color: #ff4d4f;
            font-size: 48px;
            margin-bottom: 20px;
        }
        .error-message {
            color: #333;
            margin-bottom: 20px;
        }
        .back-link {
            color: #1890ff;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
<div class="error-container">
    <div class="error-icon">
        <i class="fas fa-exclamation-circle"></i>
    </div>
    <div class="error-message">
        ${errMsg}
    </div>
    <a href="${backUrl}" class="back-link">返回</a>
</div>
</body>
</html>