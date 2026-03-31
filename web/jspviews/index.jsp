<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ page import="dao.TableDAO" %>
<%@ page import="dao.TableDaoImpl" %>
<%@ page import="model.TpTable" %>
<%@ page import="java.util.List" %>

<%
  // 检查用户是否登录
  Object user = session.getAttribute("loginuser");
  boolean isLoggedIn = (user != null);
  System.out.println("Is logged in: " + isLoggedIn);

  List<TpTable> projects = null;

  // 只有在用户登录的情况下才查询数据
  if (isLoggedIn) {
    String projectname = request.getParameter("projectname");
    String status = request.getParameter("status");
    String year = request.getParameter("year");
    String location = request.getParameter("location");

    TableDAO tableDAO = new TableDaoImpl();

    if (projectname != null || status != null || year != null || location != null) {
      projects = tableDAO.searchProjects(projectname, status, year, location);
    } else {
      projects = tableDAO.getTableByProjectnameAndYear("", "");
    }
    request.setAttribute("projects", projects);
  }
%>

<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>首页 - 旅游项目管理系统</title>
  <link rel="stylesheet" href="../css/style.css">
  <link rel="stylesheet" href="../fonts/fontawesome-free-6.4.0-web/css/all.min.css">
  <link rel="stylesheet" href="../css/index.css">
</head>
<body>
<!-- 引入导航栏 -->
<%@ include file="nav.jsp" %>

<div class="main-content">
  <div class="container">
    <c:choose>
      <c:when test="${sessionScope.loginuser != null}">
        <div class="page-header">
          <div class="header-wrapper">
            <h2><i class="fa fa-edit"></i> 旅游项目管理系统</h2>
            <p class="subtitle">欢迎回来，<span id="username">管理员</span></p>
          </div>
          <div class="quick-stats">
            <div class="stat-item">
              <i class="fa fa-check-circle"></i>
              <div class="stat-info">
                <span class="stat-value">4</span>
                <span class="stat-label">已完成</span>
              </div>
            </div>
            <div class="stat-item">
              <i class="fa fa-spinner"></i>
              <div class="stat-info">
                <span class="stat-value">3</span>
                <span class="stat-label">进行中</span>
              </div>
            </div>
            <div class="stat-item">
              <i class="fa fa-clock"></i>
              <div class="stat-info">
                <span class="stat-value">4</span>
                <span class="stat-label">计划中</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 搜索条件区域 -->
        <div class="search-area">
          <div class="search-header">
            <h3><i class="fa fa-search"></i> 搜索条件</h3>
            <button class="btn-add" onclick="window.location.href='edit-project.jsp'">
              <i class="fa fa-plus"></i> 新建项目
            </button>
          </div>
          <form id="searchForm" action="index.jsp" method="get">
            <div class="search-content">
              <div class="search-row">
                <div class="search-item">
                  <label><i class="fa fa-hashtag"></i> 项目名称</label>
                  <input type="text" name="projectname" value="${param.projectname}"
                         placeholder="请输入项目名称" class="form-control">
                </div>
                <div class="search-item">
                  <label><i class="fa fa-tag"></i> 项目状态</label>
                  <select name="status" class="form-control">
                    <option value="">全部</option>
                    <option value="已完成" ${param.status == '已完成' ? 'selected' : ''}>已完成</option>
                    <option value="进行中" ${param.status == '进行中' ? 'selected' : ''}>进行中</option>
                    <option value="计划中" ${param.status == '计划中' ? 'selected' : ''}>计划中</option>
                  </select>
                </div>
                <div class="search-item">
                  <label><i class="fa fa-calendar"></i> 年份</label>
                  <select name="year" class="form-control">
                    <option value="">全部</option>
                    <option value="2024" ${param.year == '2024' ? 'selected' : ''}>2024</option>
                    <option value="2025" ${param.year == '2025' ? 'selected' : ''}>2025</option>
                  </select>
                </div>
              </div>
              <div class="search-row">
                <div class="search-item">
                  <label><i class="fa fa-map-marker"></i> 地点</label>
                  <input type="text" name="location" value="${param.location}"
                         placeholder="请输入地点" class="form-control">
                </div>
                <div class="search-actions">
                  <button type="submit" class="btn-search">
                    <i class="fa fa-search"></i> 查询
                  </button>
                  <button type="button" class="btn-reset" onclick="resetSearch()">
                    <i class="fa fa-refresh"></i> 重置
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>

        <!-- 项目列表 -->
        <div class="project-list">
          <div class="list-header">
            <h3><i class="fa fa-list"></i> 项目列表</h3>
            <div class="list-actions">
              <button class="btn-export" onclick="exportProjects()">
                <i class="fa fa-download"></i> 导出
              </button>
              <button class="btn-batch" onclick="batchDelete()">
                <i class="fa fa-trash"></i> 批量删除
              </button>
            </div>
          </div>
          <div class="table-responsive">
            <table class="table">
              <thead>
              <tr>
                <th><input type="checkbox" id="selectAll"></th>
                <th>项目ID</th>
                <th>项目名称</th>
                <th>年份</th>
                <th>地点</th>
                <th>开始时间</th>
                <th>结束时间</th>
                <th>备注</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
              </thead>
              <tbody>
              <c:forEach items="${projects}" var="project">
                <tr>
                  <td><input type="checkbox" class="select-item"></td>
                  <td>${project.projectid}</td>
                  <td class="project-name">
                    <i class="fa fa-bookmark"></i>
                    <span>${project.projectname}</span>
                  </td>
                  <td>${project.year}</td>
                  <td><i class="fa fa-map-marker"></i> ${project.location}</td>
                  <td>${project.startdate}</td>
                  <td>${project.enddate}</td>
                  <td class="project-notes">${project.notes}</td>
                  <td><span class="status-badge status-${project.status}">${project.status}</span></td>
                  <td class="action-buttons">
                    <a href="javascript:void(0)" onclick="viewProject(${project.projectid})"
                       class="btn-action" title="查看详情">
                      <i class="fa fa-eye"></i>
                    </a>
                    <a href="javascript:void(0)" onclick="editProject(${project.projectid})"
                       class="btn-action" title="编辑">
                      <i class="fa fa-pencil"></i>
                    </a>
                    <a href="javascript:void(0)" onclick="deleteProject(${project.projectid})"
                       class="btn-action" title="删除">
                      <i class="fa fa-trash"></i>
                    </a>

                    <a href="add-team.jsp?id=${project.projectid}" class="btn-action" title="团队">
                      <i class="fas fa-users"></i></a>

                    <a href="add-expense.jsp?id=${project.projectid}" class="btn-action" title="消费">
                      <i class="fas fa-receipt"></i>
                    </a>
                    <a href="view-bill.jsp?id=${project.projectid}" class="btn-action" title="账单">
                      <i class="fas fa-file-invoice-dollar"></i>
                    </a>
                  </td>
                </tr>
              </c:forEach>
              </tbody>
            </table>
          </div>

          <!-- 分页 -->
          <div class="pagination">
            <span class="page-info">共 ${projects.size()} 条记录</span>
            <div class="page-buttons">
              <a href="#" class="btn-page" title="首页">
                <i class="fa fa-angle-double-left"></i>
              </a>
              <a href="#" class="btn-page" title="上一页">
                <i class="fa fa-angle-left"></i>
              </a>
              <a href="#" class="btn-page active">1</a>
              <a href="#" class="btn-page">2</a>
              <span class="page-ellipsis">...</span>
              <a href="#" class="btn-page" title="下一页">
                <i class="fa fa-angle-right"></i>
              </a>
              <a href="#" class="btn-page" title="末页">
                <i class="fa fa-angle-double-right"></i>
              </a>
            </div>
          </div>
        </div>
      </c:when>
      <c:otherwise>
        <div class="welcome-section">
          <div class="welcome-content">
            <i class="fa fa-globe" style="font-size: 64px; color: #007bff;"></i>
            <h1>欢迎使用旅游项目管理系统</h1>
            <p>这是一个专业的旅游项目管理平台，帮助您更好地管理旅游项目</p>
            <div class="login-prompt">
              <p>您还未登录，请先登录系统</p>
              <a href="login.jsp" class="btn-login">
                <i class="fa fa-sign-in"></i> 立即登录
              </a>
            </div>
          </div>
        </div>
      </c:otherwise>
    </c:choose>
  </div>
</div>

<script src="../js/jquery-3.6.0.min.js"></script>
<script>
  // 重置搜索
  function resetSearch() {
    window.location.href = 'index.jsp';
  }

  // 查看项目详情
  function viewProject(projectId) {
    window.location.href = 'view-project.jsp?id=' + projectId;
  }

  // 编辑项目
  function editProject(projectId) {
    window.location.href = 'edit-project.jsp?id=' + projectId;
  }

  // 删除项目
  function deleteProject(projectId) {
    if (confirm('确定要删除这个项目吗？')) {
      window.location.href = 'delete-project.jsp?id=' + projectId;
    }
  }

  // 导出项目
  function exportProjects() {
    alert('导出功能待实现');
  }

  // 批量删除
  function batchDelete() {
    const selectedItems = document.querySelectorAll('.select-item:checked');
    if (selectedItems.length === 0) {
      alert('请选择要删除的项目');
      return;
    }
    if (confirm('确定要删除选中的项目吗？')) {
      alert('批量删除功能待实现');
    }
  }

  // 全选/取消全选
  document.getElementById('selectAll').addEventListener('change', function() {
    const items = document.querySelectorAll('.select-item');
    items.forEach(item => item.checked = this.checked);
  });
</script>



</body>
</html>