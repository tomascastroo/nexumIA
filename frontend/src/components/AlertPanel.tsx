import React from 'react';
import { AlertTriangle, Info, CheckCircle, XCircle, Clock } from 'lucide-react';

interface Alert {
  id: string;
  type: 'info' | 'warning' | 'success' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  priority: 'low' | 'medium' | 'high';
}

interface AlertPanelProps {
  debtors: any[];
}

const AlertPanel: React.FC<AlertPanelProps> = ({ debtors }) => {
  const generateAlerts = (): Alert[] => {
    const alerts: Alert[] = [];
    
    // High priority debtors (debt > 10K)
    const highDebtDebtors = debtors.filter(d => parseFloat(d.custom_data?.deuda || '0') > 10000);
    if (highDebtDebtors.length > 0) {
      alerts.push({
        id: 'high-debt',
        type: 'warning',
        title: 'Deudores con Deuda Alta',
        message: `${highDebtDebtors.length} deudores tienen deudas superiores a $10,000`,
        timestamp: new Date(),
        priority: 'high'
      });
    }

    // Inactive debtors (GRIS state)
    const inactiveDebtors = debtors.filter(d => d.state === 'GRIS');
    if (inactiveDebtors.length > 0) {
      alerts.push({
        id: 'inactive-debtors',
        type: 'info',
        title: 'Deudores Inactivos',
        message: `${inactiveDebtors.length} deudores no han respondido`,
        timestamp: new Date(),
        priority: 'medium'
      });
    }

    // Successful payments
    const paidDebtors = debtors.filter(d => d.state === 'PAGADO');
    if (paidDebtors.length > 0) {
      alerts.push({
        id: 'successful-payments',
        type: 'success',
        title: 'Pagos Exitosos',
        message: `${paidDebtors.length} deudores han pagado exitosamente`,
        timestamp: new Date(),
        priority: 'low'
      });
    }

    // Pending payments
    const pendingDebtors = debtors.filter(d => d.state === 'PENDIENTE');
    if (pendingDebtors.length > 0) {
      alerts.push({
        id: 'pending-payments',
        type: 'warning',
        title: 'Pagos Pendientes',
        message: `${pendingDebtors.length} deudores tienen pagos pendientes`,
        timestamp: new Date(),
        priority: 'medium'
      });
    }

    return alerts;
  };

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'info': return <Info className="w-5 h-5 text-blue-600" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case 'success': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'error': return <XCircle className="w-5 h-5 text-red-600" />;
      default: return <Info className="w-5 h-5 text-blue-600" />;
    }
  };

  const getAlertColor = (type: Alert['type']) => {
    switch (type) {
      case 'info': return 'border-blue-200 bg-blue-50';
      case 'warning': return 'border-yellow-200 bg-yellow-50';
      case 'success': return 'border-green-200 bg-green-50';
      case 'error': return 'border-red-200 bg-red-50';
      default: return 'border-blue-200 bg-blue-50';
    }
  };

  const getPriorityColor = (priority: Alert['priority']) => {
    switch (priority) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const alerts = generateAlerts();

  if (alerts.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center text-gray-500">
          <CheckCircle className="w-8 h-8 mr-3" />
          <div>
            <h3 className="text-lg font-semibold">Todo en Orden</h3>
            <p className="text-sm">No hay alertas pendientes</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Alertas y Notificaciones</h3>
          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded-full">
            {alerts.length} alertas
          </span>
        </div>
      </div>
      
      <div className="p-6">
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 rounded-lg border ${getAlertColor(alert.type)}`}
            >
              <div className="flex items-start">
                <div className="flex-shrink-0 mt-0.5">
                  {getAlertIcon(alert.type)}
                </div>
                <div className="ml-3 flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900">{alert.title}</h4>
                    <span className={`text-xs font-medium ${getPriorityColor(alert.priority)}`}>
                      {alert.priority.toUpperCase()}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-gray-600">{alert.message}</p>
                  <div className="mt-2 flex items-center text-xs text-gray-500">
                    <Clock className="w-3 h-3 mr-1" />
                    {alert.timestamp.toLocaleTimeString('es-ES', {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-red-600">
                {alerts.filter(a => a.priority === 'high').length}
              </div>
              <div className="text-xs text-gray-600">Alta Prioridad</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-600">
                {alerts.filter(a => a.priority === 'medium').length}
              </div>
              <div className="text-xs text-gray-600">Media Prioridad</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {alerts.filter(a => a.priority === 'low').length}
              </div>
              <div className="text-xs text-gray-600">Baja Prioridad</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertPanel; 