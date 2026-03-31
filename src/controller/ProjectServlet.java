package controller;

import dao.TableDAO;
import dao.TableDaoImpl;
import model.TpTable;
import utils.DispatcherUtils;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

/**
 * 实现旅游项目管理的动作请求控制器
 */
@WebServlet(name = "ProjectServlet", value = "/jspviews/project.do")
public class ProjectServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 设置请求编码
        request.setCharacterEncoding("UTF-8");

        // 获取操作类型
        String action = request.getParameter("action");

        if (action == null) {
            listProjects(request, response);
            return;
        }

        switch (action) {
            case "add":
                addProject(request, response);
                break;
            case "edit":
                editProject(request, response);
                break;
            case "delete":
                deleteProject(request, response);
                break;
            case "view":
                viewProject(request, response);
                break;
            default:
                listProjects(request, response);
        }
    }

    private void addProject(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 获取表单数据
        String projectName = request.getParameter("projectname");
        String year = request.getParameter("year");
        String location = request.getParameter("location");
        String startDate = request.getParameter("startdate");
        String endDate = request.getParameter("enddate");
        String status = request.getParameter("status");
        String notes = request.getParameter("notes");

        // 数据校验
        if (projectName == null || projectName.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("项目名称不能为空", "edit-project.jsp", request, response);
            return;
        }

        // 创建项目对象
        TpTable project = new TpTable();
        project.setProjectname(projectName);
        project.setYear(year);
        project.setLocation(location);
        project.setStartdate(startDate);
        project.setEnddate(endDate);
        project.setStatus(status);
        project.setNotes(notes);

        // 调用DAO保存项目
        TableDAO tableDAO = new TableDaoImpl();
        int result = tableDAO.addTable(project);

        if (result > 0) {
            response.sendRedirect("index.jsp?success=true");
        } else {
            DispatcherUtils.openErrWeb("添加项目失败", "edit-project.jsp", request, response);
        }
    }

    private void editProject(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 获取项目ID和表单数据
        int projectId = Integer.parseInt(request.getParameter("projectid"));
        String projectName = request.getParameter("projectname");
        String year = request.getParameter("year");
        String location = request.getParameter("location");
        String startDate = request.getParameter("startdate");
        String endDate = request.getParameter("enddate");
        String status = request.getParameter("status");
        String notes = request.getParameter("notes");

        // 数据校验
        if (projectName == null || projectName.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("项目名称不能为空", "edit-project.jsp?id=" + projectId,
                    request, response);
            return;
        }

        // 创建项目对象
        TpTable project = new TpTable();
        project.setProjectid(projectId);
        project.setProjectname(projectName);
        project.setYear(year);
        project.setLocation(location);
        project.setStartdate(startDate);
        project.setEnddate(endDate);
        project.setStatus(status);
        project.setNotes(notes);

        // 调用DAO更新项目
        TableDAO tableDAO = new TableDaoImpl();
        boolean result = tableDAO.modifyTable(project);

        if (result) {
            response.sendRedirect("index.jsp?success=true");
        } else {
            DispatcherUtils.openErrWeb("更新项目失败",
                    "edit-project.jsp?id=" + projectId, request, response);
        }
    }

    private void deleteProject(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        int projectId = Integer.parseInt(request.getParameter("id"));

        TableDAO tableDAO = new TableDaoImpl();
        boolean result = tableDAO.removeTable(projectId);

        if (result) {
            response.sendRedirect("index.jsp?success=true");
        } else {
            DispatcherUtils.openErrWeb("删除项目失败", "index.jsp", request, response);
        }
    }

    private void viewProject(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        int projectId = Integer.parseInt(request.getParameter("id"));

        TableDAO tableDAO = new TableDaoImpl();
        TpTable project = tableDAO.getTableById(projectId);

        if (project != null) {
            request.setAttribute("project", project);
            request.getRequestDispatcher("view-project.jsp").forward(request, response);
        } else {
            DispatcherUtils.openErrWeb("项目不存在", "index.jsp", request, response);
        }
    }

    private void listProjects(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String projectname = request.getParameter("projectname");
        String status = request.getParameter("status");
        String year = request.getParameter("year");
        String location = request.getParameter("location");

        TableDAO tableDAO = new TableDaoImpl();
        List<TpTable> projects = tableDAO.searchProjects(projectname, status, year, location);

        request.setAttribute("projects", projects);
        request.getRequestDispatcher("index.jsp").forward(request, response);
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doGet(request, response);
    }
}