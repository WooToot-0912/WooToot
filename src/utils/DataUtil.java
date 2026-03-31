package utils;

import dbc.DBConnection;

import java.sql.CallableStatement;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.Arrays;

public class DataUtil extends DBConnection implements DataUtil1 {
    private Connection con = null;
    private PreparedStatement ptmt = null;
    private CallableStatement ctmt = null;
    private ResultSet rs = null;

    @Override
    public void close() {
        if (ptmt != null)
            this.closeConnection(con, ptmt, rs);//关闭表数据操作后的数据库资源
        else
            this.closeConnection(con, ctmt, rs);//关闭存储过程调用后的数据库资源

    }

    @Override
    public int insert(String sql, Object[] para) {
        int rows = 0, key = 0; //rows代表受影响行数，key代表主键为自动编号时，新记录的主键id
        try {
            con = this.getConnection();
            ptmt = con.prepareStatement(sql, PreparedStatement.RETURN_GENERATED_KEYS); //sql命令来自于调用者
            //编写算法设置参数值
            if (para != null)
                for (int i = 0; i < para.length; i++) {
                    ptmt.setObject(i + 1, para[i]);
                }
            //执行更新操作
            rows = ptmt.executeUpdate();
            System.out.println(ptmt);
            if (rows > 0) {
                rs = ptmt.getGeneratedKeys();
                if (rs != null && rs.next()) {
                    key = rs.getInt(1);//取由系统分配的主键值
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {  //不管有没有异常都会执行finally块
            this.close();
        }
        if (key > 0) return key;
        else return rows;
    }


    /*@Override
    public int update(String sql, Object[] para) {
        int rows = 0;
        try {
            con = this.getConnection();
            ptmt = con.prepareStatement(sql);
            //编写算法设置参数值
            if (para != null) {
                for (int i = 0; i < para.length; i++) {
                    ptmt.setObject(i + 1, para[i]);
                }
            }
            System.out.println(ptmt);
            rows = ptmt.executeUpdate();
        } catch (Exception e) {
            e.printStackTrace();
        }finally {
            this.close();
        }
        return rows;
    }

     */
    @Override
    public int update(String sql, Object[] para) {
        int rows = 0;
        try {
            con = this.getConnection();
            ptmt = con.prepareStatement(sql);

            if (para != null) {
                for (int i = 0; i < para.length; i++) {
                    ptmt.setObject(i + 1, para[i]);
                }
            }

            // 打印完整的SQL语句和参数
            System.out.println("执行SQL: " + sql);
            System.out.println("参数: " + Arrays.toString(para));

            rows = ptmt.executeUpdate();
            System.out.println("影响行数: " + rows);

            return rows;
        } catch (Exception e) {
            System.out.println("更新出错: " + e.getMessage());
            e.printStackTrace();
            return 0;
        } finally {
            this.close();
        }
    }

    @Override
    public int delete(String sql, Object[] para) {
        int rows = 0;
        try {
            con = this.getConnection();
            ptmt = con.prepareStatement(sql);

            if (para != null) {
                for (int i = 0; i < para.length; i++) {
                    ptmt.setObject(i+1, para[i]);
                }
            }
            System.out.println(ptmt);
            rows = ptmt.executeUpdate();
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            this.close();
        }
        return rows;
    }

    @Override
    public ResultSet select(String sql, Object[] para) {
        try {
            con = this.getConnection();
            ptmt = con.prepareStatement(sql,
                    ResultSet.TYPE_SCROLL_SENSITIVE,
                    ResultSet.CONCUR_READ_ONLY);

            if (para != null) {
                for (int i = 0; i < para.length; i++) {
                    ptmt.setObject(i + 1, para[i]);
                }
            }
            System.out.println("执行SQL: " + sql);
            System.out.println("参数: " + (para != null ? Arrays.toString(para) : "无"));
            rs = ptmt.executeQuery();
            // 确保结果集至少移动到第一行
            if (rs != null && rs.next()) {
                rs.beforeFirst(); // 将指针重置到开始位置
                return rs;
            }
            return null;
        } catch (Exception e) {
            System.out.println("查询出错: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }

    @Override
    public int selectCount(String sql, Object[] para) {
        int amount = 0;
        try {
            con = this.getConnection();
            ptmt = con.prepareStatement(sql,
                    ResultSet.TYPE_SCROLL_SENSITIVE,
                    ResultSet.CONCUR_READ_ONLY);

            if (para != null) {
                for (int i = 0; i < para.length; i++) {
                    ptmt.setObject(i + 1, para[i]);
                }
            }
            System.out.println(ptmt);
            rs = ptmt.executeQuery();
            rs.last();  //跳到最后一行
            amount = rs.getRow();  //取最后一行的行号
        } catch (Exception e) {
            e.printStackTrace();
        }finally {
            //this.close();
        }
        return amount;
    }

    @Override
    public ResultSet callProcedureWithQuery(String procName, Object[] para) {
        try {
            con = this.getConnection();
            ctmt = con.prepareCall("{ call " + procName + "}");

            if (para != null) {
                for (int i = 0; i < para.length; i++) {
                    ctmt.setObject(i + 1, para[i]);
                }
            }
            System.out.println(ctmt);
            boolean flag = ctmt.execute();
            if(flag) {
                rs = ctmt.getResultSet();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }finally{
            //this.close();
        }
        return rs;
    }
}
