package controller;

import dao.TableDAO;
import dao.TableDaoImpl;
import model.TpTable;
import utils.DispatcherUtils;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

/**
 * 项目信息更新操作请求控制器
 */
@WebServlet(name = "UpdateProjectServlet", value = "/jspviews/updateProject.do")
public class UpdateProjectServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        request.setCharacterEncoding("UTF-8");

        try {
            // 获取参数
            int projectId = Integer.parseInt(request.getParameter("projectId"));
            String projectName = request.getParameter("projectName");
            String year = request.getParameter("year");

            // 年份格式验证
            if(year == null || !year.matches("\\d{4}")) {
                DispatcherUtils.openErrWeb("年份格式不正确，请输入4位数字",
                        "edit-form.jsp?id=" + projectId, request, response);
                return;
            }

            String location = request.getParameter("location");
            String startDate = request.getParameter("startDate");
            String endDate = request.getParameter("endDate");
            String status = request.getParameter("status");
            String notes = request.getParameter("notes");

            // 其他数据校验
            if(projectName == null || projectName.trim().isEmpty()) {
                DispatcherUtils.openErrWeb("项目名称不能为空",
                        "edit-form.jsp?id=" + projectId, request, response);
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

            // 调用DAO进行更新
            TableDAO tableDAO = new TableDaoImpl();
            boolean success = tableDAO.modifyTable(project);

            if(success) {
                // 修改这里：更新成功后返回到编辑页面
                response.sendRedirect("edit-project.jsp?id=" + projectId + "&success=true");
            } else {
                DispatcherUtils.openErrWeb("项目更新失败",
                        "error.jsp?id=" + projectId, request, response);
            }

        } catch (Exception e) {
            e.printStackTrace();
            DispatcherUtils.openErrWeb("系统错误：" + e.getMessage(),
                    "edit-form.jsp", request, response);
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doGet(request, response);
    }
}