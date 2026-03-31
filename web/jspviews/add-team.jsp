<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="dao.*" %>
<%@ page import="model.*" %>
<%@ page import="java.util.List" %>
<%@ page import="java.util.ArrayList" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>

<%
  // 检查用户是否登录
  if(session.getAttribute("loginuser") == null) {
    response.sendRedirect("login.jsp");
    return;
  }

  try {
    TeammenDAO teamDAO = new TeammemDaoImpl();
    TableDAO tableDAO = new TableDaoImpl();
    UserDAO userDAO = new UserDaoImpl();  // 添加这行
    List<TpTeammems> teamMembers = null;
    TpTable project = null;
    List<TpTable> allProjects = null;
    List<TpUser> allUsers = null;  // 添加这行

    // 获取所有用户
    allUsers = userDAO.getAllUsers();  // 添加这行
    request.setAttribute("allUsers", allUsers);  // 添加这行

    // 获取项目ID参数
    String projectIdStr = request.getParameter("id");

    if (projectIdStr != null && !projectIdStr.trim().isEmpty()) {
      // 如果有项目ID，显示特定项目的团队成员
      int projectId = Integer.parseInt(projectIdStr);
      project = tableDAO.getTableById(projectId);

      if (project == null) {
        throw new IllegalArgumentException("未找到指定项目");
      }

      // 获取特定项目的团队成员
      TpTeammems member = teamDAO.getTeammemById2(projectId);
      if (member != null) {
        teamMembers = new ArrayList<>();
        teamMembers.add(member);
      }

      request.setAttribute("project", project);
    } else {
      // 如果没有项目ID，显示所有团队成员
      teamMembers = teamDAO.getAllTeamMembers();
      // 获取所有项目列表供选择
      allProjects = tableDAO.getTableByProjectnameAndYear("", "");
      request.setAttribute("allProjects", allProjects);
    }

    request.setAttribute("teamMembers", teamMembers);

  } catch (Exception e) {
    e.printStackTrace();
    response.sendRedirect("edit-project.jsp?error=" + e.getMessage());
    return;
  }
%>

<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>添加团队成员</title>
  <link rel="stylesheet" href="../css/style.css">
  <link rel="stylesheet" href="../fonts/fontawesome-free-6.4.0-web/css/all.min.css">
  <link rel="stylesheet" href="../css/add-team.css">

</head>
<body>
<%@ include file="nav.jsp" %>

<div class="main-content">
  <div class="container">
    <div class="page-header">
      <h2><i class="fa fa-users"></i> 添加团队成员</h2>
      <c:choose>
        <c:when test="${project != null}">
          <p class="subtitle">为 ${project.projectname} 添加新的团队成员</p>
        </c:when>
        <c:otherwise>
          <p class="subtitle">添加新的团队成员</p>
        </c:otherwise>
      </c:choose>
    </div>

    <!-- 添加团队成员表单 -->
    <div class="team-form">
      <form action="add-team.do" method="post" id="teamForm" onsubmit="return validateForm()">
        <c:if test="${project != null}">
          <input type="hidden" name="projectid" value="${project.projectid}">
        </c:if>
        <c:if test="${project == null}">
          <div class="form-group">
            <label for="projectid"><i class="fa fa-project-diagram"></i> 选择项目</label>
            <select id="projectid" name="projectid" required class="form-control">
              <option value="">请选择项目</option>
              <c:forEach items="${allProjects}" var="proj">
                <option value="${proj.projectid}">${proj.projectname}</option>
              </c:forEach>
            </select>
          </div>
        </c:if>

        <div class="form-group">
          <label for="teammemberid"><i class="fa fa-id-card"></i> 选择用户</label>
          <select id="teammemberid" name="teammemberid" required class="form-control">
            <option value="">请选择用户</option>
            <c:forEach items="${allUsers}" var="user">
              <option value="${user.userid}">
                  ${user.userid} - ${user.email}
                    <c:if test="${not empty user.contactnumber}">
                      (${user.contactnumber})
                    </c:if>
              </option>
            </c:forEach>
          </select>
        </div>

        <div class="form-group">
          <label for="membertype"><i class="fa fa-user-tag"></i> 成员类型</label>
          <select id="membertype" name="membertype" required class="form-control">
            <option value="">请选择成员类型</option>
            <option value="团队管理员">团队管理员</option>
            <option value="普通成员">普通成员</option>
            <option value="领队">领队</option>
            <option value="导游">导游</option>
            <option value="游客">游客</option>
            <option value="其他">其他</option>
          </select>
        </div>

        <div class="form-group">
          <label for="creationtime"><i class="fa fa-calendar"></i> 加入时间</label>
          <input type="datetime-local" id="creationtime" name="creationtime"
                 required class="form-control"
                 value="<%= new java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm").format(new java.util.Date()) %>">
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-submit">
            <i class="fa fa-user-plus"></i> 添加成员
          </button>
          <button type="button" class="btn-cancel" onclick="history.back()">
            <i class="fa fa-times"></i> 取消
          </button>
        </div>
      </form>
    </div>

    <!-- 显示团队成员列表 -->
    <div class="team-list">
      <h3><i class="fa fa-list"></i> 团队成员列表</h3>
      <div class="table-responsive">
        <table>
          <thead>
          <tr>
            <c:if test="${project == null}">
              <th>项目名称</th>
            </c:if>
            <th>成员ID</th>
            <th>成员类型</th>
            <th>加入时间</th>
            <th>操作</th>
          </tr>
          </thead>
          <tbody>
          <c:forEach items="${teamMembers}" var="member">
            <tr>
              <c:if test="${project == null}">
                <td>
                  <c:choose>
                    <c:when test="${not empty member.projectname}">
                      ${member.projectname}
                    </c:when>
                    <c:otherwise>
                      <span class="text-muted">未知项目</span>
                    </c:otherwise>
                  </c:choose>
                </td>
              </c:if>
              <td>${member.teammemberid}</td>
              <td>
                                        <span class="type-badge type-${member.membertype}">
                                            <i class="fa fa-user"></i> ${member.membertype}
                                        </span>
              </td>
              <td>${member.creationtime}</td>
              <td class="action-buttons">
                <a href="add-team.jsp?id=${member.id}" class="btn-action" title="编辑">
                  <i class="fa fa-edit"></i>
                </a>
                <a href="javascript:void(0)"
                   onclick="deleteMember(${member.teammemberid})"
                   class="btn-action"
                   title="删除">
                  <i class="fa fa-trash"></i>
                </a>
              </td>
            </tr>
          </c:forEach>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- 消息提示容器 -->
<div id="messageContainer" style="display: none;" class="message-container">
  <span id="messageText"></span>
  <button onclick="this.parentElement.style.display='none'">&times;</button>
</div>

<script>
  function validateForm() {
    var teammemberId = document.getElementById('teammemberid').value;
    var memberType = document.getElementById('membertype').value;
    var creationTime = document.getElementById('creationtime').value;

    if (!teammemberId) {
      showMessage("请输入成员ID", true);
      return false;
    }

    if (!memberType) {
      showMessage("请选择成员类型", true);
      return false;
    }

    if (!creationTime) {
      showMessage("请选择加入时间", true);
      return false;
    }

    return true;
  }

  function deleteMember(teammemberId) {
    if (confirm('确定要删除这个团队成员吗？')) {
      window.location.href = 'delete-team.jsp?id=' + teammemberId;
    }
  }

  function showMessage(message, isError) {
    var container = document.getElementById('messageContainer');
    var messageText = document.getElementById('messageText');
    container.className = 'message-container ' + (isError ? 'error' : 'success');
    messageText.textContent = message;
    container.style.display = 'block';

    setTimeout(function() {
      container.style.display = 'none';
    }, 3000);
  }

  // 检查是否需要显示消息
  var successMsg = '<%= request.getParameter("success") != null ? "true" : "false" %>';
  var errorMsg = '<%= request.getParameter("error") != null ? request.getParameter("error") : "" %>';

  if (successMsg === 'true') {
    showMessage("团队成员添加成功！", false);
  }
  if (errorMsg !== '') {
    showMessage("错误：" + errorMsg, true);
  }
</script>
</body>
</html>