package dao;

import model.TpTable;

import java.util.List;

/**
 * 旅游项目管理模块接口
 */
public interface TableDAO {
    /**
     * 添加一个新的项目信息
     * @param record
     * @return 成功返回新项目的主键值，失败返回0
     */
    public int addTable(TpTable record);

    /**
     * 修改指定的项目信息
     * @param record
     * @return 成功返回true，失败返回false
     */
    public boolean modifyTable(TpTable record);

    /**
     * 删除指定的项目信息
     * @param projectid
     * @return 成功返回true，失败返回false
     */
    public boolean removeTable(int projectid);

    /**
     * 根据项目id返回对应的项目
     * @param projectid
     * @return
     */
    public TpTable getTableById(int projectid);

    /**
     * 根据项目id返回对应的项目
     * @param projectname
     * @return
     */
    public TpTable getTableByName(String projectname);

    /**
     * 根据用户的userid查询所管理的所有的项目信息
     * @param projectid
     * @return
     */
    public List<TpTable> getTablesByUser(int projectid);



    /**
     * 根据record中非空的字段内容提供组合查询得到List<TpTable>
     * @param projectname
     * @param year
     * @return
     */
    public List<TpTable> getTableByProjectnameAndYear(String projectname, String year);

    // 添加新的多条件搜索方法
    List<TpTable> searchProjects(String projectname, String status, String year, String location);
}
