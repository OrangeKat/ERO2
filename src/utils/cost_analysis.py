import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ServerCostConfig:
    test_server_cost_per_hour: float = 0.05
    result_server_cost_per_hour: float = 0.02
    backup_storage_cost_per_gb_month: float = 0.023
    average_result_size_mb: float = 0.5
    bandwidth_cost_per_gb: float = 0.09
    cost_per_rejection: float = 0.10
    cost_per_minute_excessive_wait: float = 0.02
    acceptable_wait_time: float = 5.0
    cost_per_lost_result: float = 0.15
    simulation_duration_hours: float = 1.0


class CostAnalyzer:
    def __init__(self, config: ServerCostConfig):
        self.config = config
    
    def calculate_infrastructure_costs(
        self,
        num_test_servers: int,
        num_result_servers: int = 1,
        simulation_duration_hours: Optional[float] = None
    ) -> Dict[str, float]:
        duration = simulation_duration_hours or self.config.simulation_duration_hours
        
        test_server_cost = num_test_servers * self.config.test_server_cost_per_hour * duration
        result_server_cost = num_result_servers * self.config.result_server_cost_per_hour * duration
        total_infrastructure = test_server_cost + result_server_cost
        
        return {
            "test_servers_cost": test_server_cost,
            "result_servers_cost": result_server_cost,
            "total_infrastructure": total_infrastructure,
            "cost_per_hour": total_infrastructure / duration
        }
    
    def calculate_quality_costs(self, metrics: Dict, total_requests: int) -> Dict[str, float]:
        test_rejection_rate = metrics.get("test_queue", {}).get("blocking_rate", 0)
        result_rejection_rate = metrics.get("result_queue", {}).get("blocking_rate", 0)
        
        test_rejections = test_rejection_rate * total_requests
        result_rejections = result_rejection_rate * total_requests
        total_rejections = test_rejections + result_rejections
        
        rejection_cost = total_rejections * self.config.cost_per_rejection
        
        test_avg_wait = metrics.get("sojourn_times", {}).get("test_queue", {}).get("avg", 0)
        result_avg_wait = metrics.get("sojourn_times", {}).get("result_queue", {}).get("avg", 0)
        
        test_excessive_wait = max(0, test_avg_wait - self.config.acceptable_wait_time)
        result_excessive_wait = max(0, result_avg_wait - self.config.acceptable_wait_time)
        
        successful_requests = total_requests - total_rejections
        wait_cost = (successful_requests * (test_excessive_wait + result_excessive_wait) * 
                    self.config.cost_per_minute_excessive_wait)
        
        lost_results = result_rejections
        lost_result_cost = lost_results * self.config.cost_per_lost_result
        
        total_quality_cost = rejection_cost + wait_cost + lost_result_cost
        
        return {
            "rejection_cost": rejection_cost,
            "total_rejections": total_rejections,
            "test_rejections": test_rejections,
            "result_rejections": result_rejections,
            "wait_cost": wait_cost,
            "lost_result_cost": lost_result_cost,
            "total_quality_cost": total_quality_cost
        }
    
    def calculate_operational_costs(
        self,
        total_requests: int,
        backup_enabled: bool = False,
        avg_backup_size: Optional[int] = None
    ) -> Dict[str, float]:
        total_data_gb = (total_requests * self.config.average_result_size_mb) / 1024
        bandwidth_cost = total_data_gb * self.config.bandwidth_cost_per_gb
        
        backup_cost = 0
        if backup_enabled and avg_backup_size:
            backup_size_gb = (avg_backup_size * self.config.average_result_size_mb) / 1024
            backup_cost = (backup_size_gb * self.config.backup_storage_cost_per_gb_month * 
                          (self.config.simulation_duration_hours / (30 * 24)))
        
        total_operational = bandwidth_cost + backup_cost
        
        return {
            "bandwidth_cost": bandwidth_cost,
            "total_data_gb": total_data_gb,
            "backup_cost": backup_cost,
            "total_operational": total_operational
        }
    
    def calculate_total_cost(
        self,
        num_test_servers: int,
        metrics: Dict,
        total_requests: int,
        backup_enabled: bool = False,
        avg_backup_size: Optional[int] = None,
        simulation_duration_hours: Optional[float] = None
    ) -> Dict[str, float]:
        infrastructure = self.calculate_infrastructure_costs(
            num_test_servers, simulation_duration_hours=simulation_duration_hours
        )
        quality = self.calculate_quality_costs(metrics, total_requests)
        operational = self.calculate_operational_costs(total_requests, backup_enabled, avg_backup_size)
        
        total_cost = (infrastructure["total_infrastructure"] + 
                     quality["total_quality_cost"] + 
                     operational["total_operational"])
        
        cost_per_request = total_cost / total_requests if total_requests > 0 else 0
        successful_requests = total_requests - quality["total_rejections"]
        cost_per_successful_request = (total_cost / successful_requests 
                                       if successful_requests > 0 else float('inf'))
        
        return {
            **infrastructure,
            **quality,
            **operational,
            "total_cost": total_cost,
            "cost_per_request": cost_per_request,
            "cost_per_successful_request": cost_per_successful_request,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0
        }
    
    def calculate_roi(self, cost_result: Dict, revenue_per_request: float = 0.50) -> Dict[str, float]:
        successful_requests = cost_result["successful_requests"]
        total_revenue = successful_requests * revenue_per_request
        total_cost = cost_result["total_cost"]
        
        profit = total_revenue - total_cost
        roi_percentage = (profit / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "profit": profit,
            "roi_percentage": roi_percentage,
            "break_even_requests": total_cost / revenue_per_request if revenue_per_request > 0 else float('inf')
        }


def create_cost_config_aws_small() -> ServerCostConfig:
    return ServerCostConfig(
        test_server_cost_per_hour=0.04,
        result_server_cost_per_hour=0.02,
        backup_storage_cost_per_gb_month=0.023,
        bandwidth_cost_per_gb=0.09,
        cost_per_rejection=0.10,
        cost_per_minute_excessive_wait=0.02,
        acceptable_wait_time=5.0,
        cost_per_lost_result=0.15
    )


def create_cost_config_aws_large() -> ServerCostConfig:
    return ServerCostConfig(
        test_server_cost_per_hour=0.16,
        result_server_cost_per_hour=0.04,
        backup_storage_cost_per_gb_month=0.023,
        bandwidth_cost_per_gb=0.09,
        cost_per_rejection=0.10,
        cost_per_minute_excessive_wait=0.02,
        acceptable_wait_time=5.0,
        cost_per_lost_result=0.15
    )


def create_cost_config_onpremise() -> ServerCostConfig:
    return ServerCostConfig(
        test_server_cost_per_hour=0.08,
        result_server_cost_per_hour=0.04,
        backup_storage_cost_per_gb_month=0.01,
        bandwidth_cost_per_gb=0.0,
        cost_per_rejection=0.10,
        cost_per_minute_excessive_wait=0.02,
        acceptable_wait_time=5.0,
        cost_per_lost_result=0.15
    )