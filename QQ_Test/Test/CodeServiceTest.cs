using NUnit.Framework;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using WinFormsApp1.Models;
using WinFormsApp1.Service;
using WinFormsApp1.ServiceImpl;

namespace QQ_Test.Test
{
    [TestFixture]
    internal class CodeServiceTest
    {
        public ICodeService CodeService { get; set; }

        [SetUp]
        public void Init()
        {
            CodeService = new CodeServiceImpl();
        }

        [Test]
        public void SenfCode()
        {
            Code code = CodeService.CreateCode();
            CodeService.SendVerificationCode("1950383511@qq.com", code.NewCode);
        }

    }
}
