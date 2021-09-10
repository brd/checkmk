// Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the
// terms and conditions defined in the file COPYING, which is part of this
// source code package.

#ifndef TableStateHistory_h
#define TableStateHistory_h

#include "config.h"  // IWYU pragma: keep

#include <chrono>
#include <map>
#include <memory>
#include <string>

#include "LogCache.h"
#include "Logfile.h"
#include "Table.h"
#include "contact_fwd.h"
class Column;
class Filter;
class HostServiceState;
class LogEntry;
class MonitoringCore;
class Query;
class Row;

class TableStateHistory : public Table {
public:
    TableStateHistory(MonitoringCore *mc, LogCache *log_cache);

    [[nodiscard]] std::string name() const override;
    [[nodiscard]] std::string namePrefix() const override;
    void answerQuery(Query *query) override;
    bool isAuthorized(Row row, const contact *ctc) const override;
    [[nodiscard]] std::shared_ptr<Column> column(
        std::string colname) const override;
    static std::unique_ptr<Filter> createPartialFilter(const Query &query);

protected:
    bool _abort_query;

private:
    LogCache *_log_cache;

    // ATTENTION! All those fields below are pure evil! They are set in
    // answerQuery(), just to transport the values down the call hierarchy. The
    // really, really bad part: answerQuery() is used in a multi-threaded way
    // from the Livestatus threads, but we DO NOT have a lock/mutex to protect
    // those fields! We rely on using LogCache's mutex to protect *us*, which is
    // completely the wrong way round and highly fragile. Furthermore: All this
    // madness is not necessary, we should just pass down all the information
    // needed per query.

    // Helper functions to traverse through logfiles
    const Logfile::map_type *_entries;

    const Logfile::map_type *getEntries(Logfile *logfile);
    void getPreviousLogentry(LogCache::const_iterator &it_logs,
                             Logfile::const_iterator &it_entries);
    LogEntry *getNextLogentry(LogCache::const_iterator &it_logs,
                              Logfile::const_iterator &it_entries);
    void process(Query *query,
                 std::chrono::system_clock::duration query_timeframe,
                 HostServiceState *hs_state);
    int updateHostServiceState(
        Query *query, std::chrono::system_clock::duration query_timeframe,
        const LogEntry *entry, HostServiceState *hs_state, bool only_update,
        const std::map<std::string, int> &notification_periods);
};

#endif  // TableStateHistory_h
