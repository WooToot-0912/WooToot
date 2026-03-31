package test.junit;

import dbc.DBConnection;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.sql.Connection;

public class DBConnectionTest {

    private DBConnection dbc = null;

    @Before
    public void init(){
        dbc = new DBConnection();
    }
    @Test
    public void getConnection() throws Exception {
        //测试数据库环境是否正确，数据库连接参数是否正确
        DBConnection dbConnection = new DBConnection();
        //创建连接测试
        Connection con = dbConnection.getConnection();
        System.out.println("数据库环境配置正确，连接参数配置正确，连接成功");
        //关闭连接
        dbConnection.closeConnection(con,null,null);
    }

    @Test
    public void test(){
        System.out.println("execute test1...");
    }

    @After
    public void close(){
        System.out.println("execute test1...");
    }
}