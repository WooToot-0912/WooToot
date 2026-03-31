package controller;

import dao.TableDAO;
import dao.TableDaoImpl;
import model.TpTable;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

@WebServlet("/searchProjects")
public class ProjectSearchServlet extends HttpServlet {
    private TableDAO tableDAO = new TableDaoImpl();

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 获取搜索参数
        String projectName = request.getParameter("projectName");
        String year = request.getParameter("year");

        // 调用DAO层进行查询
        List<TpTable> projects = tableDAO.getTableByProjectnameAndYear(projectName, year);

        // 将结果存入request
        request.setAttribute("projects", projects);

        // 转发到JSP页面
        request.getRequestDispatcher("/web/jspviews/edit-project.jsp").forward(request, response);
    }
}
