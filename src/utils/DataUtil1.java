package utils;

import java.sql.ResultSet;

/**
 * 数据库访问操作接口
 * @author  zjs
 */
public interface DataUtil1 {
    /**
     * 该方法提供数据库Connection,Statement,ResultSet等操作资源的关闭
     *
     * @return void
     */
    public void close();

    /**
     * 提供数据库表记录的插入操作
     *
     * @ param sql,  提供表记录插入的用户insert into的SQL语句
     * @ param para , 当SQL中有'?'参数时，para数组提供对应参数的所有值
     * @ return int, 当主键不是自动编号时，成功返回>0,失败为0
     * 否则，返回系统分配的主键值
     */
    public int insert(String sql, Object[] para);

    /**
     * 提供数据库表记录的更新操作
     *
     * @param sql,  提供表记录更新的用户update set的SQL语句
     * @param para, 当SQL中有'?'参数时，para数组提供对应参数的所有值
     * @return boolean,  成功返回>0,失败为0
     */
    public int update(String sql, Object[] para);

    /**
     * 提供数据库表记录的删除操作
     *
     * @param sql,  提供表记录删除的用户delete from的SQL语句
     * @param para, 当SQL中有'?'参数时，para数组提供对应参数的所有值
     * @return boolean,  成功返回>0,失败为0
     */
    public int delete(String sql, Object[] para);

    /**
     * 提供表记录查询操作
     *
     * @param sql,  提供表记录查询的用户select from的SQL语句
     * @param para, 当SQL中有'?'参数时，para数组提供对应参数的所有值
     * @return ResultSet  调用后需调用接口的close()方法关闭资源
     */
    public ResultSet select(String sql, Object[] para);

    /**
     * 提供表记录查询操作，与select()不同的是返回的仅仅是查出记录的总数
     *
     * @param sql,  提供表记录查询的用户select from的SQL语句
     * @param para, 当SQL中有'?'参数时，para数组提供对应参数的所有值
     * @return int  记录数
     */
    public int selectCount(String sql, Object[] para);

    /**
     * 提供调用存储过程的数据库操作，该方法仅提供执行返回select的存储过程
     *
     * @param procName 存储过程的名称
     * @param para,    当存储过程方法中有'?'参数时，para数组提供对应参数的所有值
     * @return ResultSet
     */
    public ResultSet callProcedureWithQuery(String procName, Object[] para);

}
