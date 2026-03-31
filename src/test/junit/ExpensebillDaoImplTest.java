package test.junit;

import dao.ExpensebillDAO;
import dao.ExpensebillDaoImpl;
import model.TpExpensebill;
import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.*;

public class ExpensebillDaoImplTest {
    private ExpensebillDAO bdao = null;

    @Before
    public void init(){
        bdao = new ExpensebillDaoImpl();
    }
    @Test
    public void addBill() {
        TpExpensebill bill = new TpExpensebill();
        //bill.setBillid(1);
        bill.setProjectid(12);
        bill.setExpensetype("唱票");
        bill.setExpensetime("2024-02-02 09:00:00");
        System.out.println(bdao.addBill(bill));
    }

    @Test
    public void modifyBill() {
        TpExpensebill bill = new TpExpensebill();
        bill.setBillid(12);
        bill.setProjectid(12);
        bill.setPrice("20.00");
        bill.setExpensetype("门票");
        bill.setDescription("昆明植物园门票");
        bill.setExpensetime("2025-02-02 09:00:00");
        //bill.setInvolvedpersons("chengyuan");
        System.out.println(bdao.modifyBill(bill));
    }

    @Test
    public void removeBill() {
        System.out.println(bdao.removeBill(11));
    }

    @Test
    public void getBillById() {
        System.out.println(bdao.getBillById(1));
    }

    @Test
    public void getProjectByTeammem() {
        System.out.println(bdao.getProjectByTeammem(1));
    }
}