<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="dao.TableDAO" %>
<%@ page import="dao.TableDaoImpl" %>
<%@ page import="model.TpTable" %>

<%
    // 获取要编辑的项目ID
    String projectId = request.getParameter("id");
    TpTable project = null;

    if (projectId != null && !projectId.trim().isEmpty()) {
        TableDAO tableDAO = new TableDaoImpl();
        // 根据ID获取项目信息
        project = tableDAO.getTableById(Integer.parseInt(projectId));
    }

    if (project == null) {
        response.sendRedirect("edit-project.jsp?error=项目不存在");
        return;
    }

%>
<% if (request.getParameter("success") != null) { %>
<div class="alert alert-success">
    <i class="fa fa-check-circle"></i>
    项目信息更新成功！
</div>
<% } %>

<!DOCTYPE html>
<html lang="zh-CN">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>编辑项目</title>
    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="../fonts/fontawesome-free-6.4.0-web/css/all.min.css">
    <link rel="stylesheet" href="../css/edit-from.css">
</head>

<body>
<!-- 引入导航栏 -->
<%@ include file="nav.jsp" %>

<div class="main-content">
    <div class="container">
        <div class="page-header">
            <div class="header-wrapper">
                <h2><i class="fa fa-edit"></i> 编辑项目</h2>
                <p class="subtitle">编辑项目信息</p>
            </div>
        </div>

        <!-- 错误消息显示 -->
        <% if (request.getParameter("error") != null) { %>
        <div class="alert alert-error">
            <i class="fa fa-exclamation-circle"></i>
            <%= request.getParameter("error") %>
        </div>
        <% } %>

        <!-- 成功消息显示 -->
        <% if (request.getParameter("success") != null) { %>
        <div class="alert alert-success">
            <i class="fa fa-check-circle"></i>
            项目信息更新成功！
        </div>
        <% } %>

        <!-- 编辑项目表单 -->
        <div class="edit-project-form">
            <div class="form-header">
                <h3><i class="fa fa-pencil"></i> 修改项目信息</h3>
            </div>
            <form action="${pageContext.request.contextPath}/jspviews/updateProject.do" method="post">
                <div class="form-content">
                    <div class="form-row">
                        <div class="form-item">
                            <label><i class="fa fa-hashtag"></i> 项目ID</label>
                            <input type="text" name="projectId" required readonly
                                   value="<%= project.getProjectid() %>" class="form-control">
                        </div>
                        <div class="form-item">
                            <label><i class="fa fa-bookmark"></i> 项目名称</label>
                            <input type="text" name="projectName" required
                                   value="<%= project.getProjectname() %>" class="form-control">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-item">
                            <label><i class="fa fa-calendar"></i> 年份</label>
                            <input type="text"
                                   name="year"
                                   required
                                   pattern="[0-9]{4}"
                                   maxlength="4"
                                   oninput="this.value=this.value.replace(/[^0-9]/g,'')"
                                   value="<%= project.getYear() %>"
                                   class="form-control"
                                   placeholder="请输入4位数字年份（如：2024）">
                        </div>
                        <div class="form-item">
                            <label><i class="fa fa-map-marker"></i> 地点</label>
                            <input type="text" name="location" required
                                   value="<%= project.getLocation() %>" class="form-control">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-item">
                            <label><i class="fa fa-clock"></i> 开始时间</label>
                            <input type="date" name="startDate" required
                                   value="<%= project.getStartdate() %>" class="form-control">
                        </div>
                        <div class="form-item">
                            <label><i class="fa fa-clock"></i> 结束时间</label>
                            <input type="date" name="endDate" required
                                   value="<%= project.getEnddate() %>" class="form-control">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-item">
                            <label><i class="fa fa-tag"></i> 状态</label>
                            <select name="status" required class="form-control">
                                <option value="计划中" <%= "计划中".equals(project.getStatus()) ? "selected" : "" %>>计划中</option>
                                <option value="进行中" <%= "进行中".equals(project.getStatus()) ? "selected" : "" %>>进行中</option>
                                <option value="已完成" <%= "已完成".equals(project.getStatus()) ? "selected" : "" %>>已完成</option>
                            </select>
                        </div>
                        <div class="form-item">
                            <label><i class="fa fa-comment"></i> 备注</label>
                            <input type="text" name="notes" class="form-control"
                                   value="<%= project.getNotes() != null ? project.getNotes() : "" %>"
                                   placeholder="请输入备注信息">
                        </div>
                    </div>
                    <div class="form-actions">
                        <button type="submit" class="btn-submit">
                            <i class="fa fa-check"></i> 保存修改
                        </button>
                        <button type="button" class="btn-cancel" onclick="window.location.href='edit-project.jsp'">
                            <i class="fa fa-times"></i> 取消
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
</div>

<script src="../js/jquery-3.6.0.min.js"></script>

<!-- 添加表单验证脚本 -->
<script>
    $(document).ready(function() {
        $('form').on('submit', function(e) {
            $('input[name="year"]').on('input', function() {
                // 只允许输入数字
                this.value = this.value.replace(/[^0-9]/g, '');

                // 限制长度为4位
                if(this.value.length > 4) {
                    this.value = this.value.slice(0, 4);
                }
            });

            // 表单提交验证
            $('form').on('submit', function(e) {
                var year = $('input[name="year"]').val().trim();

                if(!year.match(/^\d{4}$/)) {
                    alert('请输入正确的4位数字年份');
                    e.preventDefault();
                    return false;
                }
            });
            // 基本验证
            var projectName = $('input[name="projectName"]').val().trim();

            var startDate = $('input[name="startDate"]').val();
            var endDate = $('input[name="endDate"]').val();

            if (!projectName) {
                alert('请输入项目名称');
                e.preventDefault();
                return false;
            }


            if (!startDate || !endDate) {
                alert('请选择开始和结束时间');
                e.preventDefault();
                return false;
            }

            // 日期比较
            if (new Date(endDate) < new Date(startDate)) {
                alert('结束时间不能早于开始时间');
                e.preventDefault();
                return false;
            }
        });
    });
</script>
</body>

</html>