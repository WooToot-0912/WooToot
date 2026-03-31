package dao;

import model.TpExpensebill;
import model.TpTable;

import java.util.List;

/**
 * 消费账单管理模块接口
 */

public interface ExpensebillDAO {
    /**
     * 添加一个新的消费账单信息
     * @param record
     * @return 成功返回新项目的主键值，失败返回0
     */
    public int addBill(TpExpensebill record);

    /**
     * 修改指定的消费账单信息
     * @param record
     * @return 成功返回true，失败返回false
     */
    public boolean modifyBill(TpExpensebill record);

    /**
     * 删除指定的消费账单信息
     * @param billid
     * @return 成功返回true，失败返回false
     */
    public  boolean removeBill(int billid);

    /**
     * 根据账单id返回对应的项目
     * @param billid
     * @return
     */
    public TpExpensebill getBillById(int billid);

    /**
     * 根据项目id查询所管理的所有成员信息
     * @param projectid
     * @return
     */
    public List<TpExpensebill> getProjectByTeammem(int projectid);
    /**
     * 获取所有消费账单信息
     * @return 所有消费账单列表
     */
    public List<TpExpensebill> getAllBills();
}
