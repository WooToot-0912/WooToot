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

@WebServlet("/SearchProjectServlet")
public class SearchProjectServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        try {
            // 获取搜索参数
            String projectname = request.getParameter("projectname");
            String status = request.getParameter("status");
            String year = request.getParameter("year");
            String location = request.getParameter("location");

            // 实例化DAO
            TableDAO dao = new TableDaoImpl();

            // 执行搜索
            List<TpTable> projects = dao.searchProjects(projectname, status, year, location);

            // 将结果存储在request中
            request.setAttribute("projects", projects);

            // 转发到JSP页面
            request.getRequestDispatcher("/jspviews/index.jsp").forward(request, response);
        } catch (Exception e) {
            e.printStackTrace();
            response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, "搜索失败：" + e.getMessage());
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doGet(request, response);
    }
}