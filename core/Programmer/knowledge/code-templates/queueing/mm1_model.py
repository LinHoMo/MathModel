"""
模板来源: resources/code-templates/queueing/mm1_model.py
修改说明: 
  - 新增M/M/1排队论模型模板
  - 支持稳态分析、蒙特卡洛模拟
"""
import numpy as np
import matplotlib.pyplot as plt


class MM1Queue:
    """M/M/1排队系统"""
    
    def __init__(self, arrival_rate, service_rate):
        """
        arrival_rate: 到达率λ（单位时间到达顾客数）
        service_rate: 服务率μ（单位时间服务顾客数）
        """
        self.lambda_ = arrival_rate
        self.mu = service_rate
        self.rho = self.lambda_ / self.mu
        
        if self.rho >= 1:
            raise ValueError(f"系统不稳定：ρ={self.rho:.2f} >= 1")
    
    def steady_state_prob(self, n):
        """系统中有n个顾客的稳态概率"""
        return self.rho ** n * (1 - self.rho)
    
    def utilization(self):
        """系统利用率"""
        return self.rho
    
    def avg_customers(self):
        """系统中平均顾客数L"""
        return self.rho / (1 - self.rho)
    
    def avg_queue_length(self):
        """队列中平均顾客数Lq"""
        return self.rho ** 2 / (1 - self.rho)
    
    def avg_time_in_system(self):
        """平均逗留时间W"""
        return 1 / (self.mu - self.lambda_)
    
    def avg_time_in_queue(self):
        """平均等待时间Wq"""
        return self.rho / (self.mu - self.lambda_)
    
    def probability_wait_longer(self, t):
        """等待时间超过t的概率"""
        return self.rho * np.exp(-self.mu * (1 - self.rho) * t)
    
    def simulate(self, n_customers, seed=42):
        """蒙特卡洛模拟"""
        np.random.seed(seed)
        
        inter_arrival = np.random.exponential(1/self.lambda_, n_customers)
        service_times = np.random.exponential(1/self.mu, n_customers)
        
        arrival_times = np.cumsum(inter_arrival)
        start_service = np.zeros(n_customers)
        end_service = np.zeros(n_customers)
        
        # 第一个顾客
        start_service[0] = arrival_times[0]
        end_service[0] = start_service[0] + service_times[0]
        
        # 后续顾客
        for i in range(1, n_customers):
            start_service[i] = max(arrival_times[i], end_service[i-1])
            end_service[i] = start_service[i] + service_times[i]
        
        wait_times = start_service - arrival_times
        time_in_system = end_service - arrival_times
        
        return {
            'arrival_times': arrival_times,
            'wait_times': wait_times,
            'time_in_system': time_in_system,
            'avg_wait': np.mean(wait_times),
            'avg_time_in_system': np.mean(time_in_system)
        }
    
    def plot_results(self, sim_result, filename='figures/mm1_queue.png'):
        """绘制结果图"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 到达时间分布
        axes[0, 0].hist(sim_result['arrival_times'], bins=20, edgecolor='black')
        axes[0, 0].set_title('到达时间分布')
        axes[0, 0].set_xlabel('时间')
        axes[0, 0].set_ylabel('频次')
        
        # 等待时间分布
        axes[0, 1].hist(sim_result['wait_times'], bins=20, edgecolor='black')
        axes[0, 1].set_title('等待时间分布')
        axes[0, 1].set_xlabel('等待时间')
        axes[0, 1].set_ylabel('频次')
        
        # 系统时间分布
        axes[1, 0].hist(sim_result['time_in_system'], bins=20, edgecolor='black')
        axes[1, 0].set_title('系统时间分布')
        axes[1, 0].set_xlabel('系统时间')
        axes[1, 0].set_ylabel('频次')
        
        # 累积顾客数
        axes[1, 1].plot(sim_result['arrival_times'], range(1, len(sim_result['arrival_times'])+1))
        axes[1, 1].set_title('累积顾客数')
        axes[1, 1].set_xlabel('时间')
        axes[1, 1].set_ylabel('顾客数')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"结果图已保存: {filename}")
    
    def report(self):
        """生成报告"""
        print("=" * 60)
        print("M/M/1 排队系统分析报告")
        print("=" * 60)
        print(f"到达率 λ: {self.lambda_:.2f} 顾客/单位时间")
        print(f"服务率 μ: {self.mu:.2f} 顾客/单位时间")
        print(f"系统利用率 ρ: {self.rho:.4f}")
        print("-" * 60)
        print(f"系统空闲概率 P₀: {1-self.rho:.4f}")
        print(f"平均顾客数 L: {self.avg_customers():.4f}")
        print(f"平均队列长度 Lq: {self.avg_queue_length():.4f}")
        print(f"平均逗留时间 W: {self.avg_time_in_system():.4f}")
        print(f"平均等待时间 Wq: {self.avg_time_in_queue():.4f}")
        print("=" * 60)


class MMcQueue:
    """M/M/c排队系统（多服务台）"""
    
    def __init__(self, arrival_rate, service_rate, n_servers):
        self.lambda_ = arrival_rate
        self.mu = service_rate
        self.c = n_servers
        self.rho = self.lambda_ / (self.c * self.mu)
        
        if self.rho >= 1:
            raise ValueError(f"系统不稳定：ρ={self.rho:.2f} >= 1")
    
    def P0(self):
        """系统空闲概率"""
        from math import factorial
        sum_terms = sum([(self.c * self.rho) ** k / factorial(k) 
                        for k in range(self.c)])
        last_term = (self.c * self.rho) ** self.c / (
            factorial(self.c) * (1 - self.rho))
        return 1 / (sum_terms + last_term)
    
    def Lq(self):
        """队列中平均顾客数"""
        p0 = self.P0()
        numerator = p0 * (self.c * self.rho) ** self.c * self.rho
        denominator = np.math.factorial(self.c) * (1 - self.rho) ** 2
        return numerator / denominator
    
    def L(self):
        """系统中平均顾客数"""
        return self.Lq() + self.c * self.rho
    
    def Wq(self):
        """平均等待时间"""
        return self.Lq() / self.lambda_
    
    def W(self):
        """平均逗留时间"""
        return self.Wq() + 1 / self.mu
    
    def report(self):
        """生成报告"""
        print("=" * 60)
        print("M/M/c 排队系统分析报告")
        print("=" * 60)
        print(f"到达率 λ: {self.lambda_:.2f} 顾客/单位时间")
        print(f"服务率 μ: {self.mu:.2f} 顾客/单位时间（每台）")
        print(f"服务台数 c: {self.c}")
        print(f"系统利用率 ρ: {self.rho:.4f}")
        print("-" * 60)
        print(f"系统空闲概率 P₀: {self.P0():.4f}")
        print(f"平均顾客数 L: {self.L():.4f}")
        print(f"平均队列长度 Lq: {self.Lq():.4f}")
        print(f"平均逗留时间 W: {self.W():.4f}")
        print(f"平均等待时间 Wq: {self.Wq():.4f}")
        print("=" * 60)


if __name__ == "__main__":
    # 示例：银行窗口
    print("排队论示例：银行窗口服务\n")
    
    # M/M/1模型
    print("【单服务台 M/M/1】")
    queue1 = MM1Queue(arrival_rate=20, service_rate=25)
    queue1.report()
    
    # 模拟
    sim_result = queue1.simulate(n_customers=1000)
    print(f"\n模拟结果:")
    print(f"  模拟平均等待时间: {sim_result['avg_wait']:.4f}")
    print(f"  模拟平均系统时间: {sim_result['avg_time_in_system']:.4f}")
    
    # M/M/c模型
    print("\n【多服务台 M/M/c】")
    queue2 = MMcQueue(arrival_rate=20, service_rate=25, n_servers=2)
    queue2.report()
