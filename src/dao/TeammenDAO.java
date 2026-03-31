package dao;


import model.TpExpensebill;
import model.TpTeammems;

import java.util.List;

/**
 * 团队成员管理模块接口
 */
public interface TeammenDAO {
    /**
     * 添加一个新的团队成员
     * @param record
     * @return 成功返回新成员的主键值，失败返回0
     */
    public  int addTeammen(TpTeammems record);

    /**
     * 修改指定的消费信息
     * @param record
     * @return 成功返回true，失败返回false
     */
    public boolean modidyTpExpensebill(TpExpensebill record);

    /**
     * 删除指定团队成员
     * @param teammemberid
     * @return 成功返回true，失败返回false
     */
    public boolean removeTeammem(int teammemberid);

    /**
     * 根据id查询团队成员
     * @param id
     * @return
     */
    public TpTeammems getTeammemById(int id);

    /**
     * 根据项目id查询团队成员
     * @param projectid
     * @return
     */
    public TpTeammems getTeammemById2(int projectid);

    TpExpensebill getBillid();
    /**
     * 获取所有团队成员信息
     * @return 所有团队成员列表
     */
    List<TpTeammems> getAllTeamMembers();
}
