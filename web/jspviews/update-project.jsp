<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="dao.TableDAO" %>
<%@ page import="dao.TableDaoImpl" %>
<%@ page import="model.TpTable" %>

<%
  request.setCharacterEncoding("UTF-8");

  try {
    // 获取表单数据
    String projectIdStr = request.getParameter("projectid");

    // 添加调试信息
    System.out.println("=== 开始处理更新请求 ===");
    System.out.println("接收到的projectId: " + projectIdStr);

    // 添加数值检查
    if (projectIdStr == null || projectIdStr.trim().isEmpty()) {
      throw new IllegalArgumentException("项目ID不能为空");
    }

    // 转换项目ID为整数
    int projectId = Integer.parseInt(projectIdStr);

    // 获取其他表单数据
    String projectName = request.getParameter("projectname");
    String year = request.getParameter("year");
    String location = request.getParameter("location");
    String status = request.getParameter("status");
    String startDate = request.getParameter("startdate");
    String endDate = request.getParameter("enddate");
    String notes = request.getParameter("notes");

    // 打印所有接收到的参数
    System.out.println("\n=== 表单数据 ===");
    System.out.println("projectId: " + projectId);
    System.out.println("projectName: " + projectName);
    System.out.println("year: " + year);
    System.out.println("location: " + location);
    System.out.println("status: " + status);
    System.out.println("startDate: " + startDate);
    System.out.println("endDate: " + endDate);
    System.out.println("notes: " + notes);

    // 检查必要字段是否为空
    if (projectName == null || projectName.trim().isEmpty() ||
            year == null || year.trim().isEmpty() ||
            location == null || location.trim().isEmpty() ||
            status == null || status.trim().isEmpty()) {
      throw new IllegalArgumentException("必要字段不能为空");
    }

    // 创建项目对象并设置值
    TpTable project = new TpTable();
    project.setProjectid(projectId);
    project.setProjectname(projectName);
    project.setYear(year);
    project.setLocation(location);
    project.setStatus(status);
    project.setStartdate(startDate);
    project.setEnddate(endDate);
    project.setNotes(notes);

    // 执行更新
    TableDAO tableDAO = new TableDaoImpl();
    boolean success = tableDAO.modifyTable(project);
    System.out.println("\n=== 更新结果 ===");
    System.out.println("更新是否成功: " + success);

    if(success) {
      response.sendRedirect("edit-project.jsp?success=true");
    } else {
      response.sendRedirect("edit-form.jsp?id=" + projectId + "&error=更新失败");
    }
  } catch(Exception e) {
    System.out.println("\n=== 发生错误 ===");
    System.out.println("错误类型: " + e.getClass().getName());
    System.out.println("错误信息: " + e.getMessage());
    e.printStackTrace();
    String projectId = request.getParameter("projectid");
    response.sendRedirect("edit-form.jsp?id=" + projectId + "&error=" + e.getMessage());
  }
%>