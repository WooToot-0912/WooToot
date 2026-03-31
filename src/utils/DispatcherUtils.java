package utils;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

/**
 * 页面跳转工具类
 */
public class DispatcherUtils {
    /**
     * 打开错误提示页面
     * @param errMsg 错误信息
     * @param backUrl 返回页面的URL
     * @param request HTTP请求对象
     * @param response HTTP响应对象
     */
    public static void openErrWeb(String errMsg, String backUrl,
                                  HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        request.setAttribute("errMsg", errMsg);
        request.setAttribute("backUrl", backUrl);
        request.getRequestDispatcher("/jspviews/error.jsp").forward(request, response);
    }

    /**
     * 打开成功提示页面
     * @param successMsg 成功信息
     * @param backUrl 返回页面的URL
     * @param request HTTP请求对象
     * @param response HTTP响应对象
     */
    public static void openSuccessWeb(String successMsg, String backUrl,
                                      HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        request.setAttribute("successMsg", successMsg);
        request.setAttribute("backUrl", backUrl);
        request.getRequestDispatcher("/jspviews/success.jsp").forward(request, response);
    }
}