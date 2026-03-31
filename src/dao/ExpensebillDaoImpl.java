package dao;

import model.TpExpensebill;
import utils.DataUtil;
import utils.DataUtil1;

import java.sql.ResultSet;
import java.util.Collections;
import java.util.List;

public class ExpensebillDaoImpl implements ExpensebillDAO{
    private DataUtil1 dataUtil = null;

    public ExpensebillDaoImpl(){
        dataUtil = new DataUtil();
    }
    @Override
    public int addBill(TpExpensebill record) {
        String sql ="insert into tp_expensebill(billid,projectid,expensetype,price,description,expensetime,involvedpersons)" +
                "values(?,?,?,?,?,?,?)";
        Object[] para ={record.getBillid(),record.getProjectid(),record.getExpensetype(),
                record.getPrice(),record.getDescription(), record.getExpensetime(),record.getInvolvedpersons()};
        int keys = dataUtil.insert(sql,para);
        return keys;
    }

    @Override
    public boolean modifyBill(TpExpensebill record) {
        String sql ="update tp_expensebill set projectid=?,expensetype=?,price=?," +
                "description=?,expensetime=?,involvedpersons=? where billid=?";
        Object[] para ={record.getProjectid(),record.getExpensetype(),
                record.getPrice(),record.getDescription(),record.getExpensetime(),record.getInvolvedpersons(),record.getBillid()};
        int rows = dataUtil.update(sql,para);
        if(rows > 0)return true;
        else return false;
    }

    @Override
    public boolean removeBill(int billid) {
        String procName ="delete from tp_expensebill where billid=?";
        Object[] para ={billid};
        try{
            int rs = dataUtil.delete(procName,para);
            if(rs>0)return true;
            else return false;
        }catch(Exception e){
            e.printStackTrace();
        }
        return false;
    }

    @Override
    public TpExpensebill getBillById(int billid) {
        String procName ="select * from tp_expensebill where billid=?";
        Object[] para ={billid};
        ResultSet rs = dataUtil.select(procName,para);
        TpExpensebill rt = new TpExpensebill(rs);
        dataUtil.close();
        return rt;
    }

    @Override
    public List<TpExpensebill> getProjectByTeammem(int projectid) {

        String sql ="select * from tp_expensebill where projectid=?";
        Object[] para ={projectid};
        ResultSet rs = dataUtil.select(sql,para);
        List<TpExpensebill> list = TpExpensebill.tranList(rs);
        dataUtil.close();
        return list;
    }


    @Override
    public List<TpExpensebill> getAllBills() {
        String sql = "SELECT e.*, t.projectname " +
                "FROM tp_expensebill e " +
                "LEFT JOIN tp_table t ON e.projectid = t.projectid " +
                "ORDER BY e.expensetime DESC";
        ResultSet rs = dataUtil.select(sql, null);
        List<TpExpensebill> list = TpExpensebill.tranList(rs);
        dataUtil.close();
        return list;
    }



}
