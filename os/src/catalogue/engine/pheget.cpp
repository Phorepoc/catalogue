// Copyright The Phorepoc Authors
// SPDX-License-Identifier: Apache-2.0

// pheget.cpp -- OURS: the download app's command line (the engine: pheget_engine.cpp). Every line goes to the debug
// log as "PH: [pheget] ..." (PhoneLab and `ph` read those).
//
//   pheget list [-all] [-index <url|path>] [-no-default]      the items that fit this device (-all: every item)
//   pheget install <id> [-drive <c|e>] [-index ...] [-no-default] [-after <pid>] [-restart <exe>]
//                                                               -after: first wait (up to 30 s) for that process to end;
//                                                               -restart: then start that exe (Catalogue's self-update)
//   pheget device                                               the board / architecture / core version the device reports
//   pheget sources                                              the default index (on/off) and the added sources
//   pheget add <url|path>  |  remove <n|url|path>               add / remove a software source (indexes.txt)
//   pheget default on|off                                       the default Phorepoc index (off needs another source)
#include <e32base.h>
#include <e32debug.h>
#include "pheget.h"

class TLogObserver : public MPheGetObserver
	{
public:
	void PheGetLog(const TDesC8& aLine) { RDebug::Printf("PH: [pheget] %S", &aLine); }
	void PheGetProgress(TInt aDone, TInt aTotal)
		{
		// one line per MB keeps the log quiet
		if (aDone / 1048576 != iLastMb)
			{
			iLastMb = aDone / 1048576;
			RDebug::Printf("PH: [pheget] %d / %d bytes", aDone, aTotal);
			}
		}
	TInt iLastMb;
	};

static TInt RunL()
	{
	TBuf<512> cmd;
	User::CommandLine(cmd);
	TLex lex(cmd);
	TPtrC verb = lex.NextToken();
	TPtrC id;
	TPtrC index;
	TBool noDefault = EFalse;
	TBool all = EFalse;
	TChar drive('c');
	TUint after = 0;
	TPtrC restart;
	for (TPtrC tok = lex.NextToken(); tok.Length(); tok.Set(lex.NextToken()))
		{
		if (tok == _L("-index"))
			index.Set(lex.NextToken());
		else if (tok == _L("-no-default"))
			noDefault = ETrue;
		else if (tok == _L("-all"))
			all = ETrue;
		else if (tok == _L("-after"))
			{
			TLex pid(lex.NextToken());
			pid.Val(after);
			}
		else if (tok == _L("-restart"))
			restart.Set(lex.NextToken());
		else if (tok == _L("-drive"))
			{
			TPtrC d = lex.NextToken();
			if (d.Length())
				drive = d[0];
			}
		else
			id.Set(tok);
		}

	// -after <pid>: the process that asked for this install (Catalogue updating itself) exits first, so the package can
	// replace its files; waits at most 30 s
	if (after)
		{
		RProcess waitFor;
		if (waitFor.Open(TProcessId(after)) == KErrNone)
			{
			TRequestStatus ended;
			waitFor.Logon(ended);
			if (ended == KRequestPending)
				{
				RTimer timer;
				TRequestStatus timeout;
				if (timer.CreateLocal() == KErrNone)
					{
					timer.After(timeout, 30000000);
					User::WaitForRequest(ended, timeout);
					if (ended == KRequestPending)
						{
						waitFor.LogonCancel(ended);
						User::WaitForRequest(ended);
						RDebug::Printf("PH: [pheget] process %u still runs after 30 s", after);
						}
					else
						{
						timer.Cancel();
						User::WaitForRequest(timeout);
						}
					timer.Close();
					}
				else
					User::WaitForRequest(ended);
				}
			waitFor.Close();
			}
		RProcess check;
		TBool ended = check.Open(TProcessId(after)) != KErrNone || check.ExitType() != EExitPending;
		check.Close();
		RDebug::Printf("PH: [pheget] process %u %s", after, ended ? "has ended" : "still runs (installing anyway)");
		}

	TLogObserver log;
	log.iLastMb = -1;
	CPheGet* get = CPheGet::NewL(log);
	CleanupStack::PushL(get);
	TInt result = KErrNone;
	if (verb == _L("device"))
		{
		RDebug::Printf("PH: [pheget] device board=%S arch=%S core=%S", &get->Board(), &get->Arch(), &get->Core());
		}
	else if (verb == _L("sources"))
		{
		CDesCArrayFlat* sources = new (ELeave) CDesCArrayFlat(4);
		CleanupStack::PushL(sources);
		get->SourcesL(*sources);
		TBool on = get->DefaultIndexEnabledL();
		TBuf8<128> def;
		def.Copy(KPheGetDefaultIndex);
		RDebug::Printf("PH: [pheget] source default %S %s", &def, on ? "on" : "off");
		for (TInt i = 0; i < sources->Count(); ++i)
			{
			TBuf8<256> s;
			s.Copy((*sources)[i].Left(256));
			RDebug::Printf("PH: [pheget] source %d %S", i, &s);
			}
		RDebug::Printf("PH: [pheget] %d added sources", sources->Count());
		CleanupStack::PopAndDestroy(sources);
		}
	else if (verb == _L("add") && id.Length())
		{
		TRAP(result, get->AddSourceL(id));
		RDebug::Printf("PH: [pheget] add: %d", result);
		}
	else if (verb == _L("remove") && id.Length())
		{
		// by number (as "pheget sources" lists them) or by the source's text
		TInt n = -1;
		TLex lexId(id);
		if (lexId.Val(n) != KErrNone || !lexId.Eos())
			{
			n = -1;
			CDesCArrayFlat* sources = new (ELeave) CDesCArrayFlat(4);
			CleanupStack::PushL(sources);
			get->SourcesL(*sources);
			for (TInt i = 0; i < sources->Count() && n < 0; ++i)
				if ((*sources)[i].CompareF(id) == 0)
					n = i;
			CleanupStack::PopAndDestroy(sources);
			}
		TRAP(result, get->RemoveSourceL(n));
		RDebug::Printf("PH: [pheget] remove: %d", result);
		}
	else if (verb == _L("default") && (id == _L("on") || id == _L("off")))
		{
		TRAP(result, get->SetDefaultIndexL(id == _L("on")));
		RDebug::Printf("PH: [pheget] default %s: %d", id == _L("on") ? "on" : "off", result);
		}
	else if (verb == _L("list"))
		{
		get->LoadIndexesL(index, noDefault);
		RArray<TPheGetItem> items;
		CleanupClosePushL(items);
		get->ItemsL(items, all);
		for (TInt i = 0; i < items.Count(); ++i)
			{
			const TPheGetItem& it = items[i];
			TPtrC8 iid = it.Id(), tag = it.Tag(), name = it.Name();
			TBuf8<32> installed;
			get->InstalledTagL(iid, installed);
			RDebug::Printf("PH: [pheget] %S %S \"%S\"%s%S", &iid, &tag, &name,
						   installed.Length() ? " installed " : "", &installed);
			}
		RDebug::Printf("PH: [pheget] %d items for board=%S arch=%S", items.Count(), &get->Board(), &get->Arch());
		CleanupStack::PopAndDestroy(&items);
		}
	else if (verb == _L("install") && id.Length())
		{
		TBuf8<64> id8;
		id8.Copy(id.Left(64));
		TRAPD(err,                                       // (trapped: -restart starts the app again whatever happens)
			get->LoadIndexesL(index, noDefault);
			TPheGetItem item;
			if (!get->FindL(id8, item))
				{
				RDebug::Printf("PH: [pheget] %S: not in any index", &id8);
				result = KErrNotFound;
				}
			else
				result = get->InstallL(item, drive);
			);
		if (err != KErrNone)
			{
			RDebug::Printf("PH: [pheget] %S: left %d", &id8, err);
			result = err;
			}
		}
	else
		{
		RDebug::Printf("PH: [pheget] usage: pheget list [-all] | install <id> [-drive c] | device | sources | add <url|path> | remove <n|url> | default on|off  [-index <url|path>] [-no-default]");
		result = KErrArgument;
		}
	CleanupStack::PopAndDestroy(get);
	if (restart.Length())
		{
		RProcess app;
		TInt err = app.Create(restart, KNullDesC);
		if (err == KErrNone)
			{
			app.Resume();
			app.Close();
			}
		TBuf8<64> name;
		name.Copy(restart.Left(64));
		RDebug::Printf("PH: [pheget] restart %S: %d", &name, err);
		}
	return result;
	}

GLDEF_C TInt E32Main()
	{
	CTrapCleanup* cleanup = CTrapCleanup::New();
	TInt err = KErrNoMemory;
	if (cleanup)
		{
		CActiveScheduler* sched = new CActiveScheduler;   // the HTTP stack's callbacks
		if (sched)
			{
			CActiveScheduler::Install(sched);
			TRAPD(leave, err = RunL());
			if (leave != KErrNone)
				{
				RDebug::Printf("PH: [pheget] left %d", leave);
				err = leave;
				}
			delete sched;
			}
		delete cleanup;
		}
	return err;
	}
