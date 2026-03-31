package dao;

import model.TpExpensebill;
import model.TpTeammems;
import utils.DataUtil;
import utils.DataUtil1;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class TeammemDaoImpl implements TeammenDAO {
    private DataUtil1 dataUtil = null;

    public TeammemDaoImpl(){
        dataUtil = new DataUtil();
    }
    @Override
    public int addTeammen(TpTeammems record) {
        String sql="insert into tp_teammems(id,projectid,teammemberid,membertype,creationtime)" +
                "values(?,?,?,?,?)";
        Object[] para ={record.getId(),record.getProjectid(),record.getTeammemberid(),
                        record.getMembertype(),record.getCreationtime()};
        int keys = dataUtil.insert(sql,para);
        return keys;
    }

    @Override
    public boolean modidyTpExpensebill(TpExpensebill record) {
        String sql="update tp_expensebill set projectid=?,expensetype=?," +
                "price=?,description=?,expensetime=?,involvedpersons=? where billid=?";
        Object[] para ={record.getProjectid(),record.getExpensetype(),record.getPrice(),
        record.getDescription(),record.getExpensetime(),record.getInvolvedpersons(),record.getBillid()};
        int rows = dataUtil.update(sql,para);
        if(rows > 0)return true;
        else return false;
    }

    @Override
    public boolean removeTeammem(int teammemberid) {
        String procName="delete from tp_teammems where teammemberid=?";
        Object[] para ={teammemberid};
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
    public TpTeammems getTeammemById(int id) {
        String sql="select * from tp_teammems where id=?";
        Object[] para ={id};
        ResultSet rs = dataUtil.select(sql,para);
        TpTeammems rt = new TpTeammems(rs);
        dataUtil.close();
        return rt;
    }
/*@Override
    public TpTeammems getTeammemById2(int projectid) {
        String sql="select * from tp_teammems where projectid=?";
        Object[] para ={projectid};
        ResultSet rs = dataUtil.select(sql,para);
        TpTeammems rt = new TpTeammems(rs);
        dataUtil.close();
        return rt;
    }*/

    @Override
    public TpExpensebill getBillid() {
        return null;
    }

    @Override
    public List<TpTeammems> getAllTeamMembers() {
        String sql = "SELECT t.*, p.projectname " +
                "FROM tp_teammems t " +
                "LEFT JOIN tp_table p ON t.projectid = p.projectid " +
                "ORDER BY t.creationtime DESC";
        ResultSet rs = null;
        List<TpTeammems> list = new ArrayList<>();
        try {
            rs = dataUtil.select(sql, null);
            while (rs != null && rs.next()) {
                TpTeammems member = new TpTeammems();
                member.setId(rs.getInt("id"));
                member.setProjectid(rs.getInt("projectid"));
                member.setTeammemberid(rs.getInt("teammemberid"));
                member.setMembertype(rs.getString("membertype"));
                member.setCreationtime(rs.getString("creationtime"));
                member.setProjectname(rs.getString("projectname"));
                list.add(member);
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            dataUtil.close();
        }
        return list;
    }

    @Override
    public TpTeammems getTeammemById2(int projectid) {
        String sql = "SELECT t.*, p.projectname " +
                "FROM tp_teammems t " +
                "LEFT JOIN tp_table p ON t.projectid = p.projectid " +
                "WHERE t.projectid = ?";
        Object[] para = {projectid};
        ResultSet rs = dataUtil.select(sql, para);
        TpTeammems member = null;
        try {
            if (rs != null && rs.next()) {
                member = new TpTeammems();
                member.setId(rs.getInt("id"));
                member.setProjectid(rs.getInt("projectid"));
                member.setTeammemberid(rs.getInt("teammemberid"));
                member.setMembertype(rs.getString("membertype"));
                member.setCreationtime(rs.getString("creationtime"));
                try {
                    member.setProjectname(rs.getString("projectname"));
                } catch (SQLException e) {
                    // 忽略这个错误
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            dataUtil.close();
        }
        return member;
    }
}
