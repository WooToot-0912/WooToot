package dbc;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

public class DBConnection {
    private String driver = "com.mysql.cj.jdbc.Driver";
    private String url = "jdbc:mysql://localhost:3306/tsasystemdb?" +
            "serverTimezone=GMT%2B8&useUnicode=true&characterEncoding=UTF-8";
    private String username = "root";
    private String pwd = "020912";

    public Connection getConnection() throws Exception {
        Class.forName(driver);

        Connection con = DriverManager.getConnection(url,username,pwd);
        System.out.println("数据库连接建立成功");
        return con;
    }

    /**
     * 数据库资源关闭方法，实现数据库对象，语句对象和结果对象的关闭操作
     * @param con Connection类型，要关闭的数据库连接对象
     * @param stmt Connection类型，要关闭的语句对象
     * @param rs Connection类型，要关闭的结果对象
     * */
    public void closeConnection(Connection con, Statement stmt, ResultSet rs) {
        try{
            if (rs != null) rs.close();
            if(stmt !=null) stmt.close();
            if(con!=null) con.close();
            System.out.println("数据库关闭成功");
        }catch(Exception e){
            e.printStackTrace();
        }
    }

}
